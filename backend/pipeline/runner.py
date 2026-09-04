import time
import logging
from database import db
from pipeline.layer1_deterministic import run_layer1
from pipeline.layer2_llm import run_layer2
from pipeline.layer3_exceptions import run_layer3

logger = logging.getLogger("pipeline_runner")

async def execute_reconciliation(batch_id: str):
    start_time = time.time()
    logger.info(f"Starting reconciliation pipeline for batch {batch_id}")

    # 1. Fetch records
    bank_rows = await db.fetch("SELECT * FROM bank_records WHERE batch_id = $1", batch_id)
    ledger_rows = await db.fetch("SELECT * FROM ledger_records WHERE batch_id = $1", batch_id)

    bank_records = [dict(r) for r in bank_rows]
    ledger_records = [dict(r) for r in ledger_rows]

    total_bank = len(bank_records)
    total_ledger = len(ledger_records)

    # 2. Layer 1: Deterministic
    l1_matches, res_bank, res_ledger = run_layer1(bank_records, ledger_records)
    logger.info(f"Layer 1 matched {len(l1_matches)} records.")

    # 3. Layer 2: LLM Fuzzy
    l2_matches, final_bank, final_ledger = await run_layer2(res_bank, res_ledger)
    logger.info(f"Layer 2 matched {len(l2_matches)} records.")

    all_matches = l1_matches + l2_matches

    # 4. Layer 3: Exceptions
    exceptions = run_layer3(batch_id, final_bank, final_ledger)

    # 5. Persist Results in Postgres
    if db.pool:
        # Clear prior results if re-running
        await db.execute("DELETE FROM match_results WHERE batch_id = $1", batch_id)
        await db.execute("DELETE FROM exceptions WHERE batch_id = $1", batch_id)

        for m in all_matches:
            await db.execute("""
                INSERT INTO match_results (batch_id, bank_id, ledger_id, layer, confidence, reason)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, batch_id, m["bank_id"], m["ledger_id"], m["layer"], m["confidence"], m["reason"])

        for e in exceptions:
            await db.execute("""
                INSERT INTO exceptions (batch_id, source, record_id, category, detail)
                VALUES ($1, $2, $3, $4, $5)
            """, batch_id, e["source"], e["record_id"], e["category"], e["detail"])

        # Calculate metrics
        match_count = len(all_matches)
        exception_count = len(exceptions)
        match_rate = round((match_count / max(total_bank, 1)) * 100, 2)

        await db.execute("""
            UPDATE batches
            SET status = 'completed',
                total_bank = $2,
                total_ledger = $3,
                matched = $4,
                exceptions = $5,
                match_rate = $6,
                updated_at = NOW()
            WHERE id = $1
        """, batch_id, total_bank, total_ledger, match_count, exception_count, match_rate)

    duration_ms = int((time.time() - start_time) * 1000)
    return {
        "batch_id": batch_id,
        "status": "completed",
        "total_bank": total_bank,
        "total_ledger": total_ledger,
        "matched": len(all_matches),
        "exceptions": len(exceptions),
        "match_rate": round((len(all_matches) / max(total_bank, 1)) * 100, 2),
        "layer_breakdown": {
            "deterministic": len(l1_matches),
            "llm": len(l2_matches)
        },
        "duration_ms": duration_ms
    }
