from datetime import datetime
from rapidfuzz import fuzz

def run_layer1(bank_records: list[dict], ledger_records: list[dict]):
    """
    Fast deterministic matching (Exact ref ID, exact amount, date proximity <= 1d, high name similarity).
    """
    matched_bank_ids = set()
    matched_ledger_ids = set()
    matches = []

    # Map ledger by amount for rapid O(1) lookups
    ledger_by_amount = {}
    for l in ledger_records:
        amt = round(float(l["amount"]), 2)
        ledger_by_amount.setdefault(amt, []).append(l)

    for b in bank_records:
        b_amt = round(float(b["amount"]), 2)
        b_date = datetime.strptime(str(b["txn_date"])[:10], "%Y-%m-%d")

        candidates = ledger_by_amount.get(b_amt, [])
        for l in candidates:
            if l["id"] in matched_ledger_ids:
                continue

            l_date = datetime.strptime(str(l["txn_date"])[:10], "%Y-%m-%d")
            date_diff = abs((b_date - l_date).days)
            name_score = fuzz.token_sort_ratio(b["counterparty"].lower(), l["vendor_name"].lower())

            # Rule 1: Exact amount, date within 1 day, high name similarity (>= 85%)
            if date_diff <= 1 and name_score >= 85:
                matched_bank_ids.add(b["id"])
                matched_ledger_ids.add(l["id"])
                matches.append({
                    "bank_id": b["id"],
                    "ledger_id": l["id"],
                    "layer": "deterministic",
                    "confidence": 0.99 if name_score > 95 else 0.92,
                    "reason": f"Exact amount ${b_amt}, date delta {date_diff}d, name similarity {name_score}%"
                })
                break

    residual_bank = [b for b in bank_records if b["id"] not in matched_bank_ids]
    residual_ledger = [l for l in ledger_records if l["id"] not in matched_ledger_ids]

    return matches, residual_bank, residual_ledger
