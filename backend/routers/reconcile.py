from fastapi import APIRouter, HTTPException
from pipeline.runner import execute_reconciliation

router = APIRouter(prefix="/api/reconcile", tags=["Reconciliation"])

@router.post("/{batch_id}")
async def reconcile_batch(batch_id: str):
    try:
        result = await execute_reconciliation(batch_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")
