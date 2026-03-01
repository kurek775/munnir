from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.news_article import NewsArticleResponse, NewsIngestResponse
from app.services.news import get_recent_articles, ingest_news

router = APIRouter(prefix="/news")


@router.post("/ingest", response_model=NewsIngestResponse)
async def ingest(
    query: str = Query(default="", description="Search query for news"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ingest_news(db, query)


@router.get("/articles", response_model=list[NewsArticleResponse])
async def list_articles(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_recent_articles(db, limit=limit)
