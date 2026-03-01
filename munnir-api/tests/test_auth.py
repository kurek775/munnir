import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_register():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/auth/register", json={
            "username": "dupuser",
            "email": "dup@example.com",
            "password": "testpass123",
        })
        resp = await client.post("/api/v1/auth/register", json={
            "username": "dupuser",
            "email": "dup2@example.com",
            "password": "testpass123",
        })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "testpass123",
        })
        resp = await client.post("/api/v1/auth/login", json={
            "username": "loginuser",
            "password": "testpass123",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass",
        })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_resp = await client.post("/api/v1/auth/register", json={
            "username": "meuser",
            "email": "me@example.com",
            "password": "testpass123",
        })
        token = reg_resp.json()["access_token"]
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "meuser"
    assert data["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_refresh_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_resp = await client.post("/api/v1/auth/register", json={
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "testpass123",
        })
        refresh_token = reg_resp.json()["refresh_token"]
        resp = await client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh_token},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_me_unauthorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401
