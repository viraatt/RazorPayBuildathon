import csv
import json
import os
import uuid
from fastapi import APIRouter
from database import db
from memory_store import put_batch
from pipeline.runner import execute_reconciliation

router = APIRouter(prefix="/api/demo", tags=["Demo"])


def _backend_data_dir() -> str:
    """backend/data – canonical location for the synthetic benchmark CSVs."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _ensure_demo_dataset() -> None:
    """Regenerate the synthetic CSVs if any is missing (fresh clone / deploy)."""
    data_dir = _backend_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    required = ["bank_feed.csv", "ledger_records.csv", "ground_truth.csv"]
    missing = [f for f in required if not os.path.exists(os.path.join(data_dir, f))]
    if missing:
        print(f"Demo dataset incomplete ({', '.join(missing)}). Regenerating via seed_data...")
        import seed_data
        seed_data.generate_dataset(output_dir=data_dir, mirror_root=False)


def find_csv(filename: str) -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    possible_paths = [
        os.path.join(_backend_data_dir(), filename),
        os.path.join(os.getcwd(), "data", filename),
        os.path.join(os.getcwd(), "..", "data", filename),
        os.path.join(here, "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "data", filename),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Could not locate {filename} for the demo dataset")


@router.post("/load")
async def load_demo_data():
    batch_id = str(uuid.uuid4())
    _ensure_demo_dataset()

    bank_csv_path = find_csv("bank_feed.csv")
    ledger_csv_path = find_csv("ledger_records.csv")

    with open(bank_csv_path, mode="r", encoding="utf-8") as f:
        bank_records = list(csv.DictReader(f))

    with open(ledger_csv_path, mode="r", encoding="utf-8") as f:
        ledger_records = list(csv.DictReader(f))

    for idx, b in enumerate(bank_records):
        b["id"] = f"b-{idx + 1}"
    for idx, l in enumerate(ledger_records):
        l["id"] = f"l-{idx + 1}"

    name = f"Demo Benchmark Batch ({len(bank_records)} bank / {len(ledger_records)} ledger)"
    use_db = db.pool is not None

    if use_db:
        try:
            await db.execute(
                """
                INSERT INTO batches (id, name, status, total_bank, total_ledger)
                VALUES ($1, $2, 'uploaded', $3, $4)
                """,
                batch_id, name, len(bank_records), len(ledger_records),
            )
            for b in bank_records:
                await db.execute(
                    """
                    INSERT INTO bank_records (batch_id, reference_id, txn_date, amount, currency, counterparty, description, raw)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    batch_id, b["reference_id"], b["txn_date"], float(b["amount"]),
                    b.get("currency", "USD"), b["counterparty"], b.get("description", ""), json.dumps(b),
                )
            for l in ledger_records:
                await db.execute(
                    """
                    INSERT INTO ledger_records (batch_id, invoice_number, txn_date, amount, currency, vendor_name, description, gl_account, raw)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    batch_id, l["invoice_number"], l["txn_date"], float(l["amount"]),
                    l.get("currency", "USD"), l["vendor_name"], l.get("description", ""),
                    l.get("gl_account", "6000-OPEX"), json.dumps(l),
                )
        except Exception as e:
            print(f"Postgres insert failed – running in-memory demo: {e}")
            use_db = False

    if not use_db:
        put_batch({
            "id": batch_id,
            "name": name,
            "status": "processing",
            "total_bank": len(bank_records),
            "total_ledger": len(ledger_records),
        })

    results = await execute_reconciliation(
        batch_id,
        bank_records=bank_records if not use_db else None,
        ledger_records=ledger_records if not use_db else None,
        force_memory=not use_db,
    )
    return results
