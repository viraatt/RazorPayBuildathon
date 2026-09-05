from fastapi import APIRouter
from database import db
from memory_store import get_batch_matches as get_store_matches

router = APIRouter(prefix="/api/matches", tags=["Matches"])


@router.get("")
async def get_matches(batch_id: str):
    if not db.pool:
        return get_store_matches(batch_id)
    query = """
        SELECT 
            m.id,
            m.layer,
            m.confidence,
            m.reason,
            b.reference_id as bank_ref,
            b.txn_date as bank_date,
            b.amount as bank_amount,
            b.counterparty as bank_counterparty,
            l.invoice_number as ledger_invoice,
            l.txn_date as ledger_date,
            l.amount as ledger_amount,
            l.vendor_name as ledger_vendor
        FROM match_results m
        JOIN bank_records b ON m.bank_id = b.id
        JOIN ledger_records l ON m.ledger_id = l.id
        WHERE m.batch_id = $1
        ORDER BY m.confidence DESC
    """
    rows = await db.fetch(query, batch_id)
    return [dict(r) for r in rows]
