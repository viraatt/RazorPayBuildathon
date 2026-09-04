# Architecture

## High-Level

## Three-Layer Matching Pipeline

### Layer 1: Deterministic Pre-Match
- pandas merge + rapidfuzz string similarity
- Exact: reference_id + amount within $0.02 + date ±1 day
- Near: amount exact + date exact + counterparty similarity >90%
- Speed: <100ms. Cost: $0.00. Handles ~60% of matches.

### Layer 2: LLM Fuzzy Resolution
- Input: Residuals from Layer 1 (~30-40%)
- Batched calls: 5-10 candidate pairs per request
- Handles: name variants, ACH lag, rounding, description parsing
- Speed: ~2s. Cost: ~$0.003.

### Layer 3: Exception Classification
- Records with confidence <0.60 or LLM says no match
- Categories: amount_mismatch, missing_party, date_drift, ambiguous_split, duplicate_conflict
