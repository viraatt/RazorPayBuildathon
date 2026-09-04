# Project Brief

## The Problem

The 2026 builder consensus: **verification capacity, not generation speed, is the bottleneck.**

Finance ops teams still reconcile bank feeds against internal ledgers by hand. A mid-size company processes 500-5,000 transactions/month. Each mismatch takes 2-5 minutes of skilled labor doing 90% pattern matching.

## What We Built

A reconciliation agent that:
- Ingests two CSV sources (bank feed + internal ledger)
- Matches via deterministic-first, LLM-second pipeline
- Reports verifiable match rate against known ground truth
- Produces an honest exception list with categorized reasons
- Runs entirely on free-tier infrastructure

## Success Criteria

| Metric | Target |
|--------|--------|
| Match rate | >85% |
| False positive rate | <5% |
| Exception clarity | Categorized with reasons |
| Throughput | 50+ records <10s |
| Cost per batch | <$0.01 |
| Infra cost | $0.00 |
