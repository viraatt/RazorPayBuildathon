from fastapi import APIRouter, HTTPException
from database import db

router = APIRouter(prefix="/api/batches", tags=["Batches"])

@router.get("")
async def list_batches():
    if not db.pool:
        return []
    rows = await db.fetch("SELECT * FROM batches ORDER BY created_at DESC LIMIT 20")
    return [dict(r) for r in rows]

@router.get("/{batch_id}")
async def get_batch(batch_id: str):
    if not db.pool:
        return {"id": batch_id, "status": "completed"}
    row = await db.fetchrow("SELECT * FROM batches WHERE id = $1", batch_id)
    if not row:
        raise HTTPException(status_code=404, detail="Batch not found")
    return dict(row)
