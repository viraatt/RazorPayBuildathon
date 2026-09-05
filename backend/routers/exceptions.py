from fastapi import APIRouter
from database import db
from memory_store import get_batch_exceptions as get_store_exceptions

router = APIRouter(prefix="/api/exceptions", tags=["Exceptions"])


@router.get("")
async def get_exceptions(batch_id: str):
    if not db.pool:
        return get_store_exceptions(batch_id)
    query = """
        SELECT 
            e.id,
            e.source,
            e.category,
            e.detail,
            e.created_at,
            CASE 
                WHEN e.source = 'bank' THEN b.reference_id
                ELSE l.invoice_number
            END as identifier,
            CASE 
                WHEN e.source = 'bank' THEN b.counterparty
                ELSE l.vendor_name
            END as entity_name,
            CASE 
                WHEN e.source = 'bank' THEN b.amount
                ELSE l.amount
            END as amount,
            CASE 
                WHEN e.source = 'bank' THEN b.txn_date
                ELSE l.txn_date
            END as txn_date
        FROM exceptions e
        LEFT JOIN bank_records b ON e.source = 'bank' AND e.record_id = b.id
        LEFT JOIN ledger_records l ON e.source = 'ledger' AND e.record_id = l.id
        WHERE e.batch_id = $1
        ORDER BY e.category, e.created_at DESC
    """
    rows = await db.fetch(query, batch_id)
    return [dict(r) for r in rows]
