from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db
from llm_router import llm_router
from routers import upload, reconcile, batches, matches, exceptions, demo

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(
    title="Finance-Ops Reconciliation Agent API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach routers
app.include_router(demo.router)
app.include_router(upload.router)
app.include_router(reconcile.router)
app.include_router(batches.router)
app.include_router(matches.router)
app.include_router(exceptions.router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "database": "connected" if db.pool else "standby",
        "llm_provider": llm_router.primary,
        "timestamp": "2026-03-31T00:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
