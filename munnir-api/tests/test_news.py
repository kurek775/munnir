import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _register_and_get_token(client: AsyncClient, username: str) -> str:
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpass123",
    })
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_ingest_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/news/ingest")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_articles_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/news/articles")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ingest_returns_valid_structure():
    """Ingest without NEWSAPI_KEY should gracefully return 0 articles."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "news_ingest")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post("/api/v1/news/ingest", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "articles_scraped" in data
    assert "articles_new" in data
    assert "articles_duplicate" in data
    assert "errors" in data
    assert isinstance(data["errors"], list)


@pytest.mark.asyncio
async def test_list_articles_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "news_list")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get("/api/v1/news/articles", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
