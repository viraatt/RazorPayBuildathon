import asyncpg
import logging
from config import settings

logger = logging.getLogger("database")

class Database:
    pool: asyncpg.Pool = None

    async def connect(self):
        if not self.pool:
            try:
                # Fix SQLAlchemy-style postgres:// if supplied by hosted providers
                db_url = settings.DATABASE_URL
                if db_url.startswith("postgres://"):
                    db_url = db_url.replace("postgres://", "postgresql://", 1)
                
                self.pool = await asyncpg.create_pool(
                    dsn=db_url,
                    min_size=2,
                    max_size=10,
                    timeout=30.0
                )
                logger.info("Connected to PostgreSQL pool.")
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed (will run in-memory fallback for demo if offline): {e}")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL pool disconnected.")

    async def execute(self, query: str, *args):
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        if not self.pool:
            return []
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

db = Database()
