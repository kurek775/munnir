import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.database import Base, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (Phase 1 convenience — Alembic used later)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start optional news scheduler
    scheduler = None
    if settings.NEWS_SCHEDULER_ENABLED:
        from app.services.scheduler import create_news_scheduler

        scheduler = create_news_scheduler()
        scheduler.start()
        logger.info("News scheduler started (interval: %dm)", settings.NEWS_SCHEDULER_INTERVAL_MINUTES)

    yield

    if scheduler is not None:
        scheduler.shutdown(wait=False)
        logger.info("News scheduler stopped")


app = FastAPI(title="Munnir API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)
