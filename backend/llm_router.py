import asyncio
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from config import settings

logger = logging.getLogger("llm_router")

# The originally bundled model (gemini-2.0-flash) has been retired by Google AI
# (HTTP 404 "no longer available"). These are verified working with the project key.
DEFAULT_MODEL = "gemini-3.6-flash"
MODEL_FALLBACKS = ["gemini-2.5-flash", "gemini-flash-latest"]


def _normalized_name_tokens(name: str) -> set[str]:
    """Lowercase tokens with entity suffixes / filler words removed."""
    if not name:
        return set()
    filler = {
        "inc", "inc.", "llc", "llp", "ltd", "corp", "corp.", "corporation",
        "co", "co.", "sa", "sarl", "gmbh", "company", "companies", "holdings",
        "group", "industries", "technologies", "tech", "labs", "the", "and",
        "of", "ltd", "llc.",
    }
    s = name.lower().replace("&", " and ").replace(",", " ").replace(".", " ")
    return {t for t in re.findall(r"[a-z0-9]+", s) if t not in filler}


class LLMRouter:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model = (
            settings.GEMINI_MODEL or os.getenv("GEMINI_MODEL", "") or DEFAULT_MODEL
        ).strip()
        self._model_chain = [self.model] + [m for m in MODEL_FALLBACKS if m != self.model]
        self.primary = "gemini" if self.gemini_key else "heuristic"
        logger.info("Initialized LLM Router provider=%s model=%s", self.primary, self.model)

    # ---------------- helpers ----------------
    @staticmethod
    def _extract_json(text: str) -> dict:
        if not text:
            raise ValueError("Empty LLM response")
        cleaned = re.sub(r"```json|```", "", text, flags=re.IGNORECASE)
        match = re.search(r"\{.*\}", cleaned, re.DOTALL | re.MULTILINE)
        if not match:
            raise ValueError("No JSON object found in LLM response")
        return json.loads(match.group(0))

    def _call_gemini(self, prompt: str) -> dict | None:
        """Try each model with retries; returns parsed JSON or None."""
        last_error = None
        for model in self._model_chain:
            for attempt in range(1, 3):
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent?key={self.gemini_key}"
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"},
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                try:
                    with urllib.request.urlopen(req, timeout=25) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    raw = data["candidates"][0]["content"]["parts"][0]["text"]
                    return self._extract_json(raw)
                except Exception as e:  # noqa: BLE001
                    last_error = e
                    logger.warning("Gemini call failed (model=%s attempt=%d): %s", model, attempt, e)
                    time.sleep(1.5 * attempt)
        logger.error("Gemini unavailable after retries: %s", last_error)
        return None

    # ---------------- public API ----------------
    async def match_candidates(self, pairs_to_evaluate: list[dict]) -> dict:
        if not pairs_to_evaluate:
            return {"matches": [], "unmatched": []}

        # No API key configured -> deterministic in-process fallback.
        if not self.gemini_key:
            return self._heuristic_fallback(pairs_to_evaluate)

        all_matches: list[dict] = []
        all_unmatched: list[dict] = []
        chunk_size = 5
        deadline = time.monotonic() + 40  # keep the demo responsive even if the API is slow
        for start in range(0, len(pairs_to_evaluate), chunk_size):
            chunk = pairs_to_evaluate[start : start + chunk_size]
            if time.monotonic() >= deadline:
                logger.warning("LLM budget exhausted; using heuristic for remaining %d pair(s)", len(chunk))
                fallback = self._heuristic_fallback(chunk)
                all_matches.extend(fallback.get("matches", []))
                all_unmatched.extend(fallback.get("unmatched", []))
                continue
            prompt = self._build_prompt(chunk)
            # The Gemini call is blocking (urllib); run it off the event loop so
            # long API timeouts do not freeze health/batches/matches endpoints.
            llm_result = await asyncio.to_thread(self._call_gemini, prompt)
            if llm_result is None:
                logger.warning("Falling back to heuristic for %d pair(s)", len(chunk))
                fallback = self._heuristic_fallback(chunk)
                all_matches.extend(fallback.get("matches", []))
                all_unmatched.extend(fallback.get("unmatched", []))
                continue
            all_matches.extend(llm_result.get("matches", []))
            all_unmatched.extend(llm_result.get("unmatched", []))

        return {"matches": all_matches, "unmatched": all_unmatched}

    def _build_prompt(self, pairs_to_evaluate: list[dict]) -> str:
        return f"""
You are a senior forensic accountant and automated reconciliation agent.
Analyze each Bank Record against its candidate Ledger Records.

Decision Rules:
1. MATCH if counterparty and vendor represent the exact same entity despite abbreviations or DBA names.
2. Allow date drift up to 3 calendar days (ACH/wire processing lag).
3. Allow minor penny rounding differences (<= $0.05).
4. DO NOT MATCH trap pairs where amount is equal but vendors are completely unrelated (e.g., Delta Air != Shell Oil).
5. If confidence is below 0.60, mark it as UNMATCHED.
6. Each ledger record may be matched at most once; do not reuse a ledger_id across matches.

Respond ONLY with valid JSON (no markdown fences) matching this schema:
{{
  "matches": [
    {{
      "bank_id": "string",
      "ledger_id": "string",
      "confidence": 0.85,
      "reason": "Detailed justification of match"
    }}
  ],
  "unmatched": [
    {{
      "bank_id": "string",
      "category": "amount_mismatch|missing_counterparty|date_drift|duplicate_conflict|fee_variance",
      "detail": "Detailed reason why no candidate matched"
    }}
  ]
}}

Input records:
{json.dumps(pairs_to_evaluate, indent=2)}
"""

    # ---------------- fallback ----------------
    def _heuristic_fallback(self, pairs_to_evaluate: list[dict]) -> dict:
        from rapidfuzz import fuzz

        matches: list[dict] = []
        unmatched: list[dict] = []
        consumed_ledger_ids: set[str] = set()

        for item in pairs_to_evaluate:
            bank = item["bank"]
            bank_id = str(bank["id"])
            best = None
            best_score = 0.0

            for cand in item["ledger_candidates"]:
                l_id = str(cand["id"])
                if l_id in consumed_ledger_ids:
                    continue
                amt_diff = abs(float(bank["amount"]) - float(cand["amount"]))
                if amt_diff > 0.10:
                    continue

                b_terms = _normalized_name_tokens(bank["counterparty"])
                l_terms = _normalized_name_tokens(cand["vendor"])
                shared = b_terms & l_terms
                jaccard = len(shared) / max(len(b_terms | l_terms), 1)
                sort_ratio = (
                    fuzz.token_set_ratio(
                        " ".join(sorted(b_terms)), " ".join(sorted(l_terms))
                    )
                    / 100.0
                )
                score = max(jaccard, sort_ratio)
                if shared and score >= 0.45 and score > best_score:
                    best = (cand, round(score, 2))
                    best_score = score

            if best:
                cand, score = best
                consumed_ledger_ids.add(str(cand["id"]))
                matches.append({
                    "bank_id": bank_id,
                    "ledger_id": str(cand["id"]),
                    "confidence": score,
                    "reason": ("Fuzzy matched entity '%s' with '%s' (similarity: %d%%)"
                               % (bank["counterparty"], cand["vendor"], int(score * 100))),
                })
            else:
                unmatched.append({
                    "bank_id": bank_id,
                    "category": "missing_counterparty",
                    "detail": ("No matching ledger candidate found for '%s' ($%.2f)"
                               % (bank["counterparty"], float(bank["amount"]))),
                })

        return {"matches": matches, "unmatched": unmatched}


llm_router = LLMRouter()