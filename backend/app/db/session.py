"""
backend/app/db/session.py
Async engine + session factory for FastAPI request handlers.

IMPORTANT: statement_cache_size=0 is REQUIRED here because Supabase's
connection pooler (port 6543) runs PgBouncer in transaction mode, which
does not support asyncpg's server-side prepared statements. Omitting
this causes intermittent DuplicatePreparedStatementError under load.
(Confirmed during Phase 0 setup — see Phase 0 Team Report §3.2.)
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"statement_cache_size": 0},
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session
