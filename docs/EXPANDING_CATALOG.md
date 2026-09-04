# Expanding the Finance-Ops Catalog

## Loop 1: Multi-Source Reconciliation ✅ (This Project)
Bank feed + Ledger → Matched pairs + exceptions

## Loop 2: Settlement Q&A Agent (Next)
Settlement statements + trade confirmations → NL answers. Add RAG layer. ~2 days.

## Loop 3: Forward Cash Forecaster
Historical cash flows + AP/AR aging → 30/60/90-day forecast. Add time-series. ~3 days.

## Loop 4: Tax-Line Matcher
GL transactions + tax rules → Tax-code assignments. Add rule engine Layer 0. ~2 days.

## Loop 5: Invoice-to-PO Matching
Invoices + POs + receipts → 3-way match. Add OCR layer. ~3 days.

## Common Pattern
Ingest → Layer 1 (rules) → Layer 2 (LLM) → Layer 3 (exceptions) → Report
