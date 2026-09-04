# Deployment Guide

All free tier. Total: $0.00/month.

## 1. Supabase (Database)
- New project → SQL Editor → run schema
- Copy DATABASE_URL from Settings → Database

## 2. Google AI Studio (LLM)
- aistudio.google.com → Get API Key → save as GEMINI_API_KEY

## 3. Render (Backend)
- New Web Service → connect repo
- Build: pip install -r backend/requirements.txt
- Start: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
- Env: DATABASE_URL, GEMINI_API_KEY

## 4. Vercel (Frontend)
- Import repo → root: frontend/
- Env: NEXT_PUBLIC_API_URL = Render URL

## 5. Keep-Alive
- GitHub → Settings → Secrets → Actions → add RENDER_URL
- .github/workflows/keepalive.yml runs automatically
