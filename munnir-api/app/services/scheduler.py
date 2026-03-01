"""Optional background scheduler for periodic news ingestion and auto-pilot."""

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)


def _run_ingest() -> None:
    """Sync wrapper that runs news ingestion in a fresh async context."""
    from app.services.news import ingest_news

    async def _do_ingest() -> None:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as db:
            result = await ingest_news(db)
            logger.info(
                "Scheduled ingest: %d scraped, %d new, %d duplicate",
                result.articles_scraped,
                result.articles_new,
                result.articles_duplicate,
            )
        await engine.dispose()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_do_ingest())
    finally:
        loop.close()


def _run_autopilot_cycles() -> None:
    """Sync wrapper that runs auto-pilot cycles for enabled sessions."""

    async def _do_autopilot() -> None:
        from app.models.trading_session import TradingSession
        from app.services.ai_analyst import analyze_session_internal
        from app.services.execution import execute_signal_internal
        from app.services.news import ingest_news

        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            # Find all active auto-pilot sessions
            result = await db.execute(
                select(TradingSession).where(
                    TradingSession.auto_pilot == True,  # noqa: E712
                    TradingSession.is_active == True,  # noqa: E712
                )
            )
            sessions = list(result.scalars().all())

            if not sessions:
                logger.debug("Auto-pilot: no active sessions")
                return

            # Ingest news once for all sessions
            await ingest_news(db)

            now = datetime.now(timezone.utc)
            interval = settings.AUTOPILOT_INTERVAL_MINUTES * 60  # seconds

            for ts in sessions:
                try:
                    # Debounce: skip if last cycle was too recent
                    if ts.last_auto_cycle_at:
                        elapsed = (now - ts.last_auto_cycle_at).total_seconds()
                        if elapsed < interval:
                            logger.debug(
                                "Auto-pilot: session %d skipped (%.0fs since last cycle)",
                                ts.id, elapsed,
                            )
                            continue

                    # Mark cycle start immediately to prevent overlap
                    ts.last_auto_cycle_at = now
                    await db.commit()

                    # Analyze
                    trade_signal = await analyze_session_internal(ts.id, db)
                    if not trade_signal:
                        logger.info("Auto-pilot: session %d — no signal produced", ts.id)
                        continue

                    # Execute or skip
                    result = await execute_signal_internal(ts.id, trade_signal.id, db)
                    logger.info(
                        "Auto-pilot: session %d — signal %d → %s",
                        ts.id, trade_signal.id,
                        result.get("type", "unknown") if result else "none",
                    )
                except Exception:
                    logger.exception("Auto-pilot: error processing session %d", ts.id)

        await engine.dispose()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_do_autopilot())
    finally:
        loop.close()


def create_news_scheduler() -> BackgroundScheduler:
    """Create a BackgroundScheduler that runs news ingestion periodically."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_ingest,
        "interval",
        minutes=settings.NEWS_SCHEDULER_INTERVAL_MINUTES,
        id="news_ingest",
        replace_existing=True,
    )

    if settings.AUTOPILOT_ENABLED:
        scheduler.add_job(
            _run_autopilot_cycles,
            "interval",
            minutes=settings.AUTOPILOT_INTERVAL_MINUTES,
            id="autopilot_cycles",
            replace_existing=True,
        )

    return scheduler
