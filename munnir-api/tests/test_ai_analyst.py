import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.ai_analyst import _build_prompt, _parse_signal


async def _register_and_get_token(client: AsyncClient, username: str) -> str:
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpass123",
    })
    return resp.json()["access_token"]


# --- Unit tests for _build_prompt ---


class _FakeSession:
    def __init__(self, *, balance=1000000, starting=1000000, risk="medium"):
        self.current_balance = balance
        self.starting_balance = starting
        self.risk_tolerance = risk


class _FakeArticle:
    def __init__(self, title="Test headline", source="Test Source", content="Some content"):
        self.title = title
        self.source = source
        self.content = content


class TestBuildPrompt:
    def _make_session(self, **kwargs):
        return _FakeSession(**kwargs)

    def _make_article(self, **kwargs):
        return _FakeArticle(**kwargs)

    def test_prompt_has_five_sections(self):
        session = self._make_session()
        articles = [self._make_article()]
        prompt = _build_prompt(session, articles)
        assert "Section 1" in prompt
        assert "Section 2" in prompt
        assert "Section 3" in prompt
        assert "Section 4" in prompt
        assert "Section 5" in prompt

    def test_prompt_includes_dollar_amounts(self):
        session = self._make_session(balance=500000, starting=1000000)
        prompt = _build_prompt(session, [])
        assert "$5,000.00" in prompt
        assert "$10,000.00" in prompt
        assert "$-5,000.00" in prompt

    def test_prompt_with_empty_articles(self):
        session = self._make_session()
        prompt = _build_prompt(session, [])
        assert "No recent news available" in prompt

    def test_prompt_includes_risk_tolerance(self):
        session = self._make_session(risk="high")
        prompt = _build_prompt(session, [])
        assert "Risk tolerance: high" in prompt


# --- Unit tests for _parse_signal ---


class TestParseSignal:
    def test_valid_json(self):
        raw = json.dumps({
            "action": "BUY",
            "asset": "AAPL",
            "conviction": 0.8,
            "reasoning": "Strong earnings report suggests continued growth",
            "risk_score": 5,
        })
        result = _parse_signal(raw)
        assert result is not None
        assert result.action == "BUY"
        assert result.asset == "AAPL"
        assert result.conviction == 0.8

    def test_invalid_json(self):
        result = _parse_signal("this is not json at all")
        assert result is None

    def test_markdown_wrapped_json(self):
        raw = '```json\n{"action":"SELL","asset":"TSLA","conviction":0.6,"reasoning":"Negative news cycle for EV sector","risk_score":7}\n```'
        result = _parse_signal(raw)
        assert result is not None
        assert result.action == "SELL"
        assert result.asset == "TSLA"

    def test_invalid_action(self):
        raw = json.dumps({
            "action": "WAIT",
            "asset": "AAPL",
            "conviction": 0.5,
            "reasoning": "Some reasoning that is long enough",
            "risk_score": 5,
        })
        result = _parse_signal(raw)
        assert result is None

    def test_out_of_range_conviction(self):
        raw = json.dumps({
            "action": "BUY",
            "asset": "AAPL",
            "conviction": 1.5,
            "reasoning": "Some reasoning that is long enough",
            "risk_score": 5,
        })
        result = _parse_signal(raw)
        assert result is None


# --- Integration tests (endpoint level) ---


@pytest.mark.asyncio
async def test_analyze_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/sessions/1/analyze")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_signals_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/sessions/1/signals")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_analyze_nonexistent_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "ai_nonexist")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post("/api/v1/sessions/99999/analyze", headers=headers)
    assert resp.status_code in (404, 503)


@pytest.mark.asyncio
async def test_signals_empty_for_new_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "ai_empty_sigs")
        headers = {"Authorization": f"Bearer {token}"}
        create_resp = await client.post("/api/v1/sessions", json={
            "session_name": "AI Test Session",
            "starting_balance": 5000.0,
        }, headers=headers)
        session_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/sessions/{session_id}/signals", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []
