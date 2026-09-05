from fastapi import APIRouter, HTTPException
from database import db
from memory_store import get_batch as get_store_batch, list_batches as list_store_batches

router = APIRouter(prefix="/api/batches", tags=["Batches"])


@router.get("")
async def list_batches():
    if not db.pool:
        return list_store_batches()
    rows = await db.fetch("SELECT * FROM batches ORDER BY created_at DESC LIMIT 20")
    return [dict(r) for r in rows]


@router.get("/{batch_id}")
async def get_batch(batch_id: str):
    if not db.pool:
        row = get_store_batch(batch_id)
        if not row:
            raise HTTPException(status_code=404, detail="Batch not found")
        return row
    row = await db.fetchrow("SELECT * FROM batches WHERE id = $1", batch_id)
    if not row:
        raise HTTPException(status_code=404, detail="Batch not found")
    return dict(row)
