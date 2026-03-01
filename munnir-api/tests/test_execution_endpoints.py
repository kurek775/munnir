"""Integration tests for execution endpoints (auth, empty states, 404s)."""

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


# ── Auth 401 Tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/sessions/1/signals/1/execute")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_skip_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/sessions/1/signals/1/skip")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_trades_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/sessions/1/trades")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_positions_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/sessions/1/positions")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_close_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/sessions/1/positions/1/close")
    assert resp.status_code == 401


# ── Empty State Tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_trades():
    """New session should have no trades."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "ep_empty_trades")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post("/api/v1/sessions", json={
            "session_name": "Empty Trades",
            "starting_balance": 1000.0,
        }, headers=headers)
        session_id = resp.json()["id"]
        resp = await client.get(f"/api/v1/sessions/{session_id}/trades", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_empty_positions():
    """New session should have no positions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "ep_empty_pos")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post("/api/v1/sessions", json={
            "session_name": "Empty Positions",
            "starting_balance": 1000.0,
        }, headers=headers)
        session_id = resp.json()["id"]
        resp = await client.get(
            f"/api/v1/sessions/{session_id}/positions", headers=headers
        )
    assert resp.status_code == 200
    assert resp.json() == []


# ── 404 Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_nonexistent_session():
    """Execute on nonexistent session returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "ep_exec_404_s")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            "/api/v1/sessions/99999/signals/1/execute", headers=headers
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_trades_nonexistent_session():
    """Trades on nonexistent session returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "ep_trades_404")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get(
            "/api/v1/sessions/99999/trades", headers=headers
        )
    assert resp.status_code == 404
