import csv
import io
import json
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from database import db

router = APIRouter(prefix="/api/upload", tags=["Upload"])

@router.post("")
async def upload_csvs(
    name: str = Form("Manual Upload Batch"),
    bank_csv: UploadFile = File(...),
    ledger_csv: UploadFile = File(...)
):
    batch_id = str(uuid.uuid4())

    try:
        bank_content = (await bank_csv.read()).decode("utf-8")
        ledger_content = (await ledger_csv.read()).decode("utf-8")

        bank_reader = csv.DictReader(io.StringIO(bank_content))
        ledger_reader = csv.DictReader(io.StringIO(ledger_content))

        bank_records = list(bank_reader)
        ledger_records = list(ledger_reader)

        if db.pool:
            # Create Batch
            await db.execute("""
                INSERT INTO batches (id, name, status, total_bank, total_ledger)
                VALUES ($1, $2, 'uploaded', $3, $4)
            """, batch_id, name, len(bank_records), len(ledger_records))

            # Insert Bank records
            for b in bank_records:
                await db.execute("""
                    INSERT INTO bank_records (batch_id, reference_id, txn_date, amount, currency, counterparty, description, raw)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, batch_id, b.get("reference_id", "N/A"), b["txn_date"], float(b["amount"]), b.get("currency", "USD"), b["counterparty"], b.get("description", ""), json.dumps(b))

            # Insert Ledger records
            for l in ledger_records:
                await db.execute("""
                    INSERT INTO ledger_records (batch_id, invoice_number, txn_date, amount, currency, vendor_name, description, gl_account, raw)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, batch_id, l.get("invoice_number", "N/A"), l["txn_date"], float(l["amount"]), l.get("currency", "USD"), l["vendor_name"], l.get("description", ""), l.get("gl_account", "6000-OPEX"), json.dumps(l))

        return {
            "batch_id": batch_id,
            "status": "uploaded",
            "bank_records_count": len(bank_records),
            "ledger_records_count": len(ledger_records)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV files: {str(e)}")
