import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_hello_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/hello")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cpp_result"] == 42
    assert data["message"] == "Hello from Munnir!"
