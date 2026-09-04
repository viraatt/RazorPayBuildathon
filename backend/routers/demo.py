import csv
import json
import os
import uuid
from fastapi import APIRouter
from database import db
from pipeline.runner import execute_reconciliation

router = APIRouter(prefix="/api/demo", tags=["Demo"])

@router.post("/load")
async def load_demo_data():
    """
    1-Click Demo endpoint for presentation/judges:
    Loads pre-seeded data from data/ and runs full reconciliation loop.
    """
    batch_id = str(uuid.uuid4())
    bank_csv_path = "data/bank_feed.csv" if os.path.exists("data/bank_feed.csv") else "../data/bank_feed.csv"
    ledger_csv_path = "data/ledger_records.csv" if os.path.exists("data/ledger_records.csv") else "../data/ledger_records.csv"

    with open(bank_csv_path, mode="r", encoding="utf-8") as f:
        bank_records = list(csv.DictReader(f))

    with open(ledger_csv_path, mode="r", encoding="utf-8") as f:
        ledger_records = list(csv.DictReader(f))

    if db.pool:
        # Create Batch
        await db.execute("""
            INSERT INTO batches (id, name, status, total_bank, total_ledger)
            VALUES ($1, 'Demo Benchmark Batch (58 records)', 'uploaded', $2, $3)
        """, batch_id, len(bank_records), len(ledger_records))

        for b in bank_records:
            await db.execute("""
                INSERT INTO bank_records (batch_id, reference_id, txn_date, amount, currency, counterparty, description, raw)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, batch_id, b["reference_id"], b["txn_date"], float(b["amount"]), b.get("currency", "USD"), b["counterparty"], b.get("description", ""), json.dumps(b))

        for l in ledger_records:
            await db.execute("""
                INSERT INTO ledger_records (batch_id, invoice_number, txn_date, amount, currency, vendor_name, description, gl_account, raw)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, batch_id, l["invoice_number"], l["txn_date"], float(l["amount"]), l.get("currency", "USD"), l["vendor_name"], l.get("description", ""), l.get("gl_account", "6000-OPEX"), json.dumps(l))

    # Run complete reconciliation loop
    results = await execute_reconciliation(batch_id)
    return results
