import json
import logging
import os
from config import settings

logger = logging.getLogger("llm_router")

class LLMRouter:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        
        self.primary = "gemini" if self.gemini_key else ("groq" if self.groq_key else "mock")
        logger.info(f"Initialized LLM Router with primary provider: {self.primary}")

    async def match_candidates(self, pairs_to_evaluate: list[dict]) -> dict:
        """
        pairs_to_evaluate format:
        [
          {
             "bank": {"id": "...", "ref": "...", "date": "...", "amount": 100.0, "counterparty": "..."},
             "ledger_candidates": [ {"id": "...", "inv": "...", "date": "...", "amount": 100.0, "vendor": "..."} ]
          }
        ]
        """
        if not pairs_to_evaluate:
            return {"matches": [], "unmatched": []}

        prompt = f"""
You are a senior forensic accountant and automated reconciliation agent.
Analyze each Bank Record against its candidate Ledger Records.

Decision Rules:
1. MATCH if counterparty and vendor represent the exact same entity despite abbreviations, DBA names, or entity suffixes (e.g. "Acme Corp LLC" == "Acme Corporation").
2. Allow date drift up to 3 calendar days (ACH/wire processing lag).
3. Allow minor penny rounding differences (<= $0.05) or explicit wire fee surcharges.
4. DO NOT MATCH trap pairs where amount is equal but vendors are completely unrelated (e.g., "Delta Air Lines" != "Shell Oil").
5. If confidence is below 0.60 or counterparties mismatch, mark it as UNMATCHED with a clear category.

Respond ONLY with valid JSON matching this schema:
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

Input records for evaluation:
{json.dumps(pairs_to_evaluate, indent=2)}
"""

        # 1. Try Gemini
        if self.gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=self.gemini_key)
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                return json.loads(response.text)
            except Exception as e:
                logger.warning(f"Gemini resolution failed: {e}. Attempting fallback...")

        # 2. Try Groq Fallback
        if self.groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_key)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a financial reconciliation JSON agent."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                return json.loads(completion.choices[0].message.content)
            except Exception as e:
                logger.error(f"Groq fallback failed: {e}")

        # 3. Deterministic Heuristic Fallback if API keys are missing/rate-limited
        logger.info("Using built-in heuristic semantic matching fallback.")
        return self._heuristic_fallback(pairs_to_evaluate)

    def _heuristic_fallback(self, pairs_to_evaluate: list[dict]) -> dict:
        from rapidfuzz import fuzz
        matches = []
        unmatched = []

        for item in pairs_to_evaluate:
            b = item["bank"]
            best_match = None
            highest_score = 0.0

            for l in item["ledger_candidates"]:
                amt_diff = abs(float(b["amount"]) - float(l["amount"]))
                name_sim = fuzz.token_sort_ratio(b["counterparty"].lower(), l["vendor"].lower()) / 100.0

                if amt_diff <= 0.10 and name_sim > 0.65:
                    if name_sim > highest_score:
                        highest_score = name_sim
                        best_match = (l, name_sim)

            if best_match:
                l_cand, score = best_match
                matches.append({
                    "bank_id": b["id"],
                    "ledger_id": l_cand["id"],
                    "confidence": round(score, 2),
                    "reason": f"Fuzzy matched entity '{b['counterparty']}' with '{l_cand['vendor']}' (sim: {int(score*100)}%)"
                })
            else:
                unmatched.append({
                    "bank_id": b["id"],
                    "category": "missing_counterparty",
                    "detail": f"No ledger candidate found for {b['counterparty']} with amount {b['amount']}"
                })

        return {"matches": matches, "unmatched": unmatched}

llm_router = LLMRouter()
