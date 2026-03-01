"""News ingestion service — NewsAPI + RSS feeds, with deduplication."""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.news_article import NewsArticle
from app.schemas.news_article import NewsIngestResponse

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("NYT Business", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"),
]


def _content_hash(title: str, source: str) -> str:
    return hashlib.sha256(f"{title}|{source}".encode()).hexdigest()


async def _fetch_newsapi(query: str) -> list[dict]:
    """Fetch articles from NewsAPI /v2/everything."""
    if not settings.NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY not set, skipping NewsAPI fetch")
        return []

    params = {
        "q": query or "geopolitics OR markets OR economy",
        "sortBy": "publishedAt",
        "pageSize": settings.NEWS_MAX_ARTICLES,
        "apiKey": settings.NEWSAPI_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{settings.NEWSAPI_BASE_URL}/everything", params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("articles", [])
    except Exception as e:
        logger.error("NewsAPI fetch failed: %s", e)
        return []


async def _fetch_rss_feeds() -> list[dict]:
    """Fetch articles from RSS feeds (run feedparser in thread)."""
    articles = []
    for name, url in RSS_FEEDS:
        try:
            feed = await asyncio.to_thread(feedparser.parse, url)
            for entry in feed.entries[: settings.NEWS_MAX_ARTICLES]:
                articles.append(
                    {
                        "title": entry.get("title", ""),
                        "source": name,
                        "url": entry.get("link", ""),
                        "content": entry.get("summary", entry.get("description", "")),
                        "author": entry.get("author"),
                        "published_at": entry.get("published"),
                    }
                )
        except Exception as e:
            logger.error("RSS feed %s failed: %s", name, e)
    return articles


def _parse_published_at(value: str | None) -> datetime | None:
    """Best-effort parse of published date strings."""
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


async def ingest_news(db: AsyncSession, query: str = "") -> NewsIngestResponse:
    """Fetch news from all sources, deduplicate, store new articles."""
    errors: list[str] = []

    # Fetch from both sources concurrently
    newsapi_articles, rss_articles = await asyncio.gather(
        _fetch_newsapi(query),
        _fetch_rss_feeds(),
    )

    # Normalize NewsAPI articles
    raw_articles = []
    for a in newsapi_articles:
        raw_articles.append(
            {
                "title": a.get("title", ""),
                "source": a.get("source", {}).get("name", "unknown"),
                "url": a.get("url", ""),
                "content": a.get("content") or a.get("description", ""),
                "summary": a.get("description"),
                "author": a.get("author"),
                "published_at": a.get("publishedAt"),
            }
        )
    raw_articles.extend(rss_articles)

    total_scraped = len(raw_articles)
    new_count = 0
    dup_count = 0

    for article in raw_articles:
        if not article["title"] or not article["url"]:
            continue

        h = _content_hash(article["title"], article["source"])

        # Check for duplicates by hash or URL
        existing = await db.execute(
            select(NewsArticle).where(
                (NewsArticle.content_hash == h) | (NewsArticle.url == article["url"])
            )
        )
        if existing.scalar_one_or_none():
            dup_count += 1
            continue

        try:
            db.add(
                NewsArticle(
                    title=article["title"],
                    source=article["source"],
                    url=article["url"],
                    content=article["content"],
                    summary=article.get("summary"),
                    author=article.get("author"),
                    published_at=_parse_published_at(article.get("published_at")),
                    content_hash=h,
                )
            )
            new_count += 1
        except Exception as e:
            errors.append(f"Failed to store article '{article['title'][:50]}': {e}")

    await db.commit()

    return NewsIngestResponse(
        articles_scraped=total_scraped,
        articles_new=new_count,
        articles_duplicate=dup_count,
        errors=errors,
    )


async def get_recent_articles(
    db: AsyncSession, limit: int = 20, max_age_hours: int | None = None
) -> list[NewsArticle]:
    """Fetch recent articles, optionally filtered by age."""
    stmt = select(NewsArticle).order_by(NewsArticle.scraped_at.desc()).limit(limit)
    if max_age_hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        stmt = stmt.where(NewsArticle.scraped_at >= cutoff)
    result = await db.execute(stmt)
    return list(result.scalars().all())
