# Scope

## In Scope (v1)

- Synthetic bank feed CSV (~58 records) + ledger CSV (~62 records)
- Ground truth labels for evaluation
- Pre-seeded demo data (one-click)
- Layer 1: Deterministic matching (exact ref, amount ±$0.02, date ±1 day)
- Layer 2: LLM fuzzy matching (Gemini 2.0 Flash primary, Groq fallback)
- Layer 3: Exception classification (5 categories)
- Confidence scoring (0.00-1.00)
- CSV upload UI (drag-and-drop)
- Dashboard with KPI cards, matches table, exceptions panel
- PostgreSQL database (Supabase)
- FastAPI backend (Render)
- Next.js frontend (Vercel)
- GitHub Actions keep-alive
- All free tier

## Out of Scope

- Real bank/ERP API integration
- Multi-currency conversion
- User auth and multi-tenancy
- Audit trail / compliance
- Real-time streaming
- Human-in-the-loop override UI
