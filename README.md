# Finance-Ops Reconciler

> **Verification capacity, not generation speed, is the bottleneck.**
> This agent closes the multi-source reconciliation loop across 50+ record batches,
> reporting its match rate and the exceptions it could not resolve.

## What It Does

Upload a **Bank Feed CSV** and an **Internal Ledger CSV**. The system:

1. **Layer 1 — Deterministic Match**: Exact reference ID + amount ±$0.02 + date ±1 day
2. **Layer 2 — LLM Fuzzy Resolution**: Gemini 3.6 Flash resolves name variants, rounding, ACH lag
3. **Layer 3 — Exception Classification**: Unmatched records categorized with reasons

## Quick Start

### Demo Mode
Click **"Load Benchmark Demo"** in the dashboard to run the synthetic 53-bank / 62-ledger reconciliation
(regenerated automatically by `seed_data.py` if the CSVs are missing).

### Manual Upload
1. Upload Bank Feed CSV + Internal Ledger CSV
2. Click **Start Reconciliation**
3. View matches, confidence scores, and exceptions

## Tech Stack

| Layer | Technology | Hosting | Cost |
|-------|-----------|---------|------|
| Frontend | Next.js 15, React 19, shadcn/ui | Vercel | Free |
| Backend | FastAPI, asyncpg | Render | Free |
| Database | PostgreSQL 16 | Supabase | Free |
| LLM | Gemini 3.6 Flash (primary) | Google AI | Free |
| LLM Fallback | Local deterministic heuristic | In-process | Free |
| Keep-alive | GitHub Actions cron | GitHub | Free |

**Total monthly cost: $0.00**

## Architecture




See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full design.

## Documentation

- [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) — Problem statement
- [docs/SCOPE.md](docs/SCOPE.md) — In/out of scope
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design
- [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) — DB schema, API, prompts
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Deployment guide
- [docs/EXPANDING_CATALOG.md](docs/EXPANDING_CATALOG.md) — Future loops
- [docs/PROGRESS.md](docs/PROGRESS.md) — Build log

## Results (Demo Batch)

> 53 bank records vs 62 ledger entries (regenerated deterministically by `seed_data.py`, seed 42).
> Layer 1 (Deterministic): 25 exact pairs in ~7ms. Layer 2 (Gemini 3.6 Flash): 15 fuzzy pairs.
> **Benchmark: 40/40 matchable pairs matched — precision 100%, recall 100%, F1 1.0.**
> 5/5 trap pairs correctly rejected, 35 forensic exceptions classified. Cost: ~$0.

## License

MIT
