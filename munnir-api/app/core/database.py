import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


# ── Lightweight migration helper (adds missing columns to existing SQLite DBs) ──

_MIGRATIONS: list[tuple[str, str, str]] = [
    # (table, column, ALTER TABLE statement)
    ("trading_sessions", "auto_pilot", "ALTER TABLE trading_sessions ADD COLUMN auto_pilot BOOLEAN DEFAULT 0 NOT NULL"),
    ("trading_sessions", "last_auto_cycle_at", "ALTER TABLE trading_sessions ADD COLUMN last_auto_cycle_at DATETIME"),
    ("trading_sessions", "auto_pilot_interval_minutes", "ALTER TABLE trading_sessions ADD COLUMN auto_pilot_interval_minutes INTEGER DEFAULT 15 NOT NULL"),
]


async def run_migrations(eng: AsyncEngine) -> None:
    """Check for missing columns and add them via ALTER TABLE."""
    async with eng.begin() as conn:
        for table, column, ddl in _MIGRATIONS:
            rows = await conn.execute(text(f"PRAGMA table_info({table})"))
            existing = {r[1] for r in rows.fetchall()}
            if column not in existing:
                await conn.execute(text(ddl))
                logger.info("Migration: added column %s.%s", table, column)
