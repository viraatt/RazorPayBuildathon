from datetime import datetime
from llm_router import llm_router

async def run_layer2(residual_bank: list[dict], residual_ledger: list[dict]):
    """
    Batched LLM semantic fuzzy match on residuals.
    """
    if not residual_bank or not residual_ledger:
        return [], residual_bank, residual_ledger

    # Form candidate pairs for the LLM
    batch_payload = []
    for b in residual_bank:
        b_amt = float(b["amount"])
        b_date = datetime.strptime(str(b["txn_date"])[:10], "%Y-%m-%d")

        # Ledger candidates within amount delta <= $10.00 and date delta <= 4 days
        candidates = []
        for l in residual_ledger:
            l_amt = float(l["amount"])
            l_date = datetime.strptime(str(l["txn_date"])[:10], "%Y-%m-%d")
            
            amt_diff = abs(b_amt - l_amt)
            date_diff = abs((b_date - l_date).days)

            if amt_diff <= 10.00 and date_diff <= 4:
                candidates.append({
                    "id": str(l["id"]),
                    "invoice": l.get("invoice_number", ""),
                    "date": str(l["txn_date"])[:10],
                    "amount": float(l["amount"]),
                    "vendor": l["vendor_name"],
                    "description": l.get("description", "")
                })

        if candidates:
            batch_payload.append({
                "bank": {
                    "id": str(b["id"]),
                    "reference": b.get("reference_id", ""),
                    "date": str(b["txn_date"])[:10],
                    "amount": float(b["amount"]),
                    "counterparty": b["counterparty"],
                    "description": b.get("description", "")
                },
                "ledger_candidates": candidates
            })

    if not batch_payload:
        return [], residual_bank, residual_ledger

    llm_result = await llm_router.match_candidates(batch_payload)
    llm_matches = llm_result.get("matches", [])

    matched_bank_ids = set()
    matched_ledger_ids = set()
    formatted_matches = []

    for m in llm_matches:
        if m.get("confidence", 0) >= 0.60:
            formatted_matches.append({
                "bank_id": m["bank_id"],
                "ledger_id": m["ledger_id"],
                "layer": "llm",
                "confidence": float(m["confidence"]),
                "reason": m["reason"]
            })
            matched_bank_ids.add(m["bank_id"])
            matched_ledger_ids.add(m["ledger_id"])

    final_residual_bank = [b for b in residual_bank if str(b["id"]) not in matched_bank_ids]
    final_residual_ledger = [l for l in residual_ledger if str(l["id"]) not in matched_ledger_ids]

    return formatted_matches, final_residual_bank, final_residual_ledger
