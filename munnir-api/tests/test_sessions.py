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
async def test_create_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "sess_create")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post("/api/v1/sessions", json={
            "session_name": "My First Session",
            "starting_balance": 10000.0,
            "risk_tolerance": "medium",
        }, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_name"] == "My First Session"
    assert data["starting_balance"] == 10000.0
    assert data["current_balance"] == 10000.0
    assert data["risk_tolerance"] == "medium"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_sessions():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "sess_list")
        headers = {"Authorization": f"Bearer {token}"}
        await client.post("/api/v1/sessions", json={
            "session_name": "Session A",
            "starting_balance": 5000.0,
        }, headers=headers)
        await client.post("/api/v1/sessions", json={
            "session_name": "Session B",
            "starting_balance": 8000.0,
        }, headers=headers)
        resp = await client.get("/api/v1/sessions", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "sess_get")
        headers = {"Authorization": f"Bearer {token}"}
        create_resp = await client.post("/api/v1/sessions", json={
            "session_name": "Detail Session",
            "starting_balance": 1000.0,
        }, headers=headers)
        session_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["session_name"] == "Detail Session"


@pytest.mark.asyncio
async def test_update_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "sess_update")
        headers = {"Authorization": f"Bearer {token}"}
        create_resp = await client.post("/api/v1/sessions", json={
            "session_name": "Old Name",
            "starting_balance": 2000.0,
        }, headers=headers)
        session_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/sessions/{session_id}", json={
            "session_name": "New Name",
            "risk_tolerance": "high",
        }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_name"] == "New Name"
    assert data["risk_tolerance"] == "high"


@pytest.mark.asyncio
async def test_delete_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "sess_delete")
        headers = {"Authorization": f"Bearer {token}"}
        create_resp = await client.post("/api/v1/sessions", json={
            "session_name": "To Delete",
            "starting_balance": 500.0,
        }, headers=headers)
        session_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/sessions/{session_id}", headers=headers)
        assert resp.status_code == 204
        # Verify it's gone
        resp = await client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_sessions_require_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/sessions")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_session_ownership():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a = await _register_and_get_token(client, "owner_a")
        token_b = await _register_and_get_token(client, "owner_b")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        create_resp = await client.post("/api/v1/sessions", json={
            "session_name": "A's Session",
            "starting_balance": 1000.0,
        }, headers=headers_a)
        session_id = create_resp.json()["id"]

        # User B should not see User A's session
        resp = await client.get(f"/api/v1/sessions/{session_id}", headers=headers_b)
        assert resp.status_code == 404
