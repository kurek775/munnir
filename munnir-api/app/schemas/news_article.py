from datetime import datetime

from pydantic import BaseModel


class NewsArticleResponse(BaseModel):
    id: int
    title: str
    source: str
    url: str
    content: str
    summary: str | None
    author: str | None
    published_at: datetime | None
    content_hash: str
    scraped_at: datetime

    model_config = {"from_attributes": True}


class NewsIngestResponse(BaseModel):
    articles_scraped: int
    articles_new: int
    articles_duplicate: int
    errors: list[str]
