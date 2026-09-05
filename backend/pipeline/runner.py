import logging
import time
from datetime import datetime, timezone

from database import db
from llm_router import llm_router as llm
from memory_store import put_batch, get_batch_records, put_batch_exceptions, put_batch_matches
from pipeline.layer1_deterministic import run_layer1
from pipeline.layer2_llm import run_layer2
from pipeline.layer3_exceptions import run_layer3

logger = logging.getLogger("pipeline_runner")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_store_rows(all_matches, exceptions, bank_records, ledger_records, final_bank, final_ledger):
    """Shape match/exception rows exactly like the DB JOIN endpoints so the
    frontend tables keep working in in-memory (no Postgres) mode."""
    bank_by_id = {str(b["id"]): b for b in bank_records}
    ledger_by_id = {str(l["id"]): l for l in ledger_records}

    match_rows = []
    for idx, m in enumerate(all_matches, 1):
        b = bank_by_id.get(str(m["bank_id"]), {})
        l = ledger_by_id.get(str(m["ledger_id"]), {})
        match_rows.append({
            "id": f"m-{idx}",
            "layer": m.get("layer", "llm"),
            "confidence": float(m.get("confidence", 0)),
            "reason": m.get("reason", ""),
            "bank_ref": b.get("reference_id", ""),
            "bank_date": str(b.get("txn_date", ""))[:10],
            "bank_amount": float(b.get("amount", 0) or 0),
            "bank_counterparty": b.get("counterparty", ""),
            "ledger_invoice": l.get("invoice_number", ""),
            "ledger_date": str(l.get("txn_date", ""))[:10],
            "ledger_amount": float(l.get("amount", 0) or 0),
            "ledger_vendor": l.get("vendor_name", ""),
        })

    exc_rows = []
    for idx, e in enumerate(exceptions, 1):
        pool = final_bank if e["source"] == "bank" else final_ledger
        rec = {}
        for r in pool:
            if str(r.get("id")) == str(e.get("record_id")):
                rec = r
                break
        if e["source"] == "bank":
            identifier = rec.get("reference_id", "")
            entity = rec.get("counterparty", "")
        else:
            identifier = rec.get("invoice_number", "")
            entity = rec.get("vendor_name", "")
        exc_rows.append({
            "id": f"e-{idx}",
            "source": e["source"],
            "category": e["category"],
            "detail": e["detail"],
            "created_at": _iso_now(),
            "identifier": identifier,
            "entity_name": entity,
            "amount": float(rec.get("amount", 0) or 0),
            "txn_date": str(rec.get("txn_date", ""))[:10],
        })

    return match_rows, exc_rows


async def execute_reconciliation(
    batch_id: str,
    bank_records: list[dict] | None = None,
    ledger_records: list[dict] | None = None,
    force_memory: bool = False,
):
    """Run the 3-layer reconciliation pipeline.

    - When the Postgres pool is reachable (and force_memory is False) records are
      loaded from the DB and every result row is persisted there.
    - Otherwise the caller may pass records in and results are kept in the
      in-memory store so the demo works fully offline.
    """
    start_time = time.time()
    use_db = (db.pool is not None) and not force_memory

    if use_db:
        bank_rows = await db.fetch("SELECT * FROM bank_records WHERE batch_id = $1", batch_id)
        ledger_rows = await db.fetch("SELECT * FROM ledger_records WHERE batch_id = $1", batch_id)
        bank_records = [dict(r) for r in bank_rows]
        ledger_records = [dict(r) for r in ledger_rows]
    else:
        if bank_records is None or ledger_records is None:
            bank_records, ledger_records = get_batch_records(batch_id)
        bank_records = list(bank_records or [])
        ledger_records = list(ledger_records or [])

    total_bank = len(bank_records)
    total_ledger = len(ledger_records)
    logger.info("Reconciliation %s started (%d bank / %d ledger)", batch_id, total_bank, total_ledger)

    # Layer 1: Deterministic
    l1_matches, res_bank, res_ledger = run_layer1(bank_records, ledger_records)
    logger.info("Layer 1 matched %d records.", len(l1_matches))

    # Layer 2: LLM fuzzy
    l2_matches, final_bank, final_ledger = await run_layer2(res_bank, res_ledger)
    logger.info("Layer 2 matched %d records.", len(l2_matches))

    all_matches = l1_matches + l2_matches

    # Layer 3: Exceptions / forensic refusal
    exceptions = run_layer3(batch_id, final_bank, final_ledger)

    match_count = len(all_matches)
    exception_count = len(exceptions)
    match_rate = round((match_count / max(total_bank, 1)) * 100, 2)
    duration_ms = int((time.time() - start_time) * 1000)

    if use_db:
        # Clear prior results before re-running.
        await db.execute("DELETE FROM match_results WHERE batch_id = $1", batch_id)
        await db.execute("DELETE FROM exceptions WHERE batch_id = $1", batch_id)

        for m in all_matches:
            await db.execute(
                """
                INSERT INTO match_results (batch_id, bank_id, ledger_id, layer, confidence, reason)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                batch_id, m["bank_id"], m["ledger_id"], m["layer"], m["confidence"], m["reason"],
            )

        for e in exceptions:
            await db.execute(
                """
                INSERT INTO exceptions (batch_id, source, record_id, category, detail)
                VALUES ($1, $2, $3, $4, $5)
                """,
                batch_id, e["source"], e["record_id"], e["category"], e["detail"],
            )

        await db.execute(
            """
            UPDATE batches
            SET status = 'completed',
                total_bank = $2,
                total_ledger = $3,
                matched = $4,
                exceptions = $5,
                match_rate = $6,
                updated_at = NOW()
            WHERE id = $1
            """,
            batch_id, total_bank, total_ledger, match_count, exception_count, match_rate,
        )
    else:
        match_rows, exc_rows = _build_store_rows(
            all_matches, exceptions, bank_records, ledger_records, final_bank, final_ledger
        )
        put_batch({
            "id": batch_id,
            "status": "completed",
            "total_bank": total_bank,
            "total_ledger": total_ledger,
            "matched": match_count,
            "exceptions": exception_count,
            "match_rate": match_rate,
            "llm_model": llm.model,
            "layer_breakdown": {"deterministic": len(l1_matches), "llm": len(l2_matches)},
            "duration_ms": duration_ms,
        })
        put_batch_matches(batch_id, match_rows)
        put_batch_exceptions(batch_id, exc_rows)

    return {
        "batch_id": batch_id,
        "status": "completed",
        "total_bank": total_bank,
        "total_ledger": total_ledger,
        "matched": match_count,
        "exceptions": exception_count,
        "match_rate": match_rate,
        "layer_breakdown": {
            "deterministic": len(l1_matches),
            "llm": len(l2_matches),
        },
        "duration_ms": duration_ms,
    }