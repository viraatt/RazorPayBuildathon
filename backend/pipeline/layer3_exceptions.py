def run_layer3(batch_id: str, unmatched_bank: list[dict], unmatched_ledger: list[dict]) -> list[dict]:
    """
    Classify unresolved transactions with forensic failure reasons.
    """
    exceptions = []

    for b in unmatched_bank:
        desc = b.get("description", "").lower()
        cp = b.get("counterparty", "").lower()
        amt = float(b["amount"])

        if "fee" in desc or "charge" in desc or "nsf" in desc or "surcharge" in desc:
            category = "fee_variance"
            detail = f"Unmatched bank debit for fee/charge: '{b['counterparty']}' (${amt:.2f})"
        elif "tax" in desc or "franchise" in cp:
            category = "missing_counterparty"
            detail = f"Statutory tax/levy debit with no ledger invoice registered: ${amt:.2f}"
        else:
            category = "missing_counterparty"
            detail = f"No matching ERP invoice found for '{b['counterparty']}' (${amt:.2f})"

        exceptions.append({
            "batch_id": batch_id,
            "source": "bank",
            "record_id": b["id"],
            "category": category,
            "detail": detail
        })

    for l in unmatched_ledger:
        amt = float(l["amount"])
        exceptions.append({
            "batch_id": batch_id,
            "source": "ledger",
            "record_id": l["id"],
            "category": "uncleared_accrual",
            "detail": f"Booked AP invoice for '{l['vendor_name']}' (${amt:.2f}) has not cleared bank feed"
        })

    return exceptions
