"""
Async Database Engine & Session
================================
Uses SQLAlchemy async engine with asyncpg driver.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings

# ── Async Engine ────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# ── Session Factory ─────────────────────────────────────────────
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency that yields an async DB session."""
    async with async_session_maker() as session:
        yield session


async def create_db_and_tables() -> None:
    """Create all SQLModel tables (used for dev/testing, Alembic is preferred)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
