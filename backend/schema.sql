-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables for fresh migration
DROP TABLE IF EXISTS exceptions CASCADE;
DROP TABLE IF EXISTS match_results CASCADE;
DROP TABLE IF EXISTS ledger_records CASCADE;
DROP TABLE IF EXISTS bank_records CASCADE;
DROP TABLE IF EXISTS batches CASCADE;

-- 1. Batches Table: tracks reconciliation jobs
CREATE TABLE batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(30) DEFAULT 'uploaded', -- uploaded, processing, completed, failed
    total_bank INT DEFAULT 0,
    total_ledger INT DEFAULT 0,
    matched INT DEFAULT 0,
    exceptions INT DEFAULT 0,
    match_rate DECIMAL(5, 2) DEFAULT 0.00,
    llm_model VARCHAR(50) DEFAULT 'gemini-2.0-flash',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Bank Feed Records
CREATE TABLE bank_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    reference_id VARCHAR(100) NOT NULL,
    txn_date DATE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    counterparty VARCHAR(255) NOT NULL,
    description TEXT,
    raw JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Internal Ledger Records
CREATE TABLE ledger_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    invoice_number VARCHAR(100) NOT NULL,
    txn_date DATE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    vendor_name VARCHAR(255) NOT NULL,
    description TEXT,
    gl_account VARCHAR(50) DEFAULT '6000-OPEX',
    raw JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Match Results (Reconciliation Output)
CREATE TABLE match_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    bank_id UUID NOT NULL REFERENCES bank_records(id) ON DELETE CASCADE,
    ledger_id UUID NOT NULL REFERENCES ledger_records(id) ON DELETE CASCADE,
    layer VARCHAR(20) NOT NULL, -- deterministic | llm
    confidence DECIMAL(4, 3) NOT NULL, -- 0.000 to 1.000
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_bank_match UNIQUE (batch_id, bank_id),
    CONSTRAINT unique_ledger_match UNIQUE (batch_id, ledger_id)
);

-- 5. Exceptions (Unresolved Records)
CREATE TABLE exceptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    source VARCHAR(10) NOT NULL, -- bank | ledger
    record_id UUID NOT NULL,
    category VARCHAR(50) NOT NULL, -- amount_mismatch, missing_counterparty, date_drift, duplicate_conflict, fee_variance
    detail TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance Indexes
CREATE INDEX idx_bank_records_batch ON bank_records(batch_id);
CREATE INDEX idx_ledger_records_batch ON ledger_records(batch_id);
CREATE INDEX idx_match_results_batch ON match_results(batch_id);
CREATE INDEX idx_exceptions_batch ON exceptions(batch_id);
CREATE INDEX idx_bank_amount_date ON bank_records(amount, txn_date);
CREATE INDEX idx_ledger_amount_date ON ledger_records(amount, txn_date);
