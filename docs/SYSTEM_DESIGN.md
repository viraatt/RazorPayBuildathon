# System Design

## Database Schema

### batches
id (UUID PK), name, status (uploaded|processing|complete|failed), total_bank, total_ledger, matched, exceptions, match_rate, llm_model, created_at

### bank_records
id (UUID PK), batch_id (FK), txn_date, amount, currency, counterparty, description, reference_id, raw (JSONB)

### ledger_records
id (UUID PK), batch_id (FK), txn_date, amount, currency, vendor_name, invoice_number, description, gl_account, raw (JSONB)

### match_results
id (UUID PK), batch_id (FK), bank_id (FK), ledger_id (FK), layer (deterministic|llm), confidence (0-1), reason

### exceptions
id (UUID PK), batch_id (FK), source (bank|ledger), record_id, category, detail

## API Contracts

- POST /api/upload — multipart CSV → { batch_id, counts }
- POST /api/reconcile/{batch_id} — run pipeline → { match_rate, matched, exceptions }
- GET /api/batches — list runs
- GET /api/matches?batch_id=x — paginated matches
- GET /api/exceptions?batch_id=x — categorized exceptions
- GET /api/health — keep-alive ping

## LLM Prompt

System: You are a financial reconciliation agent. Determine if record pairs represent the same transaction. Consider name similarity, amount differences (rounding/fees), date proximity (ACH lag), description overlap. Respond in JSON schema with matches[] and unmatched[].
