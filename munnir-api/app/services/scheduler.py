"""Optional background scheduler for periodic news ingestion."""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
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
    return scheduler
