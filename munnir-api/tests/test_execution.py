"""Tests for execution service (mocked prices)."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _setup_session_and_signal(
    client: AsyncClient,
    headers: dict,
    balance: float = 10000.0,
    action: str = "BUY",
    asset: str = "AAPL",
    conviction: float = 0.8,
    risk_tolerance: str = "medium",
) -> tuple[int, int]:
    """Helper: create a session and manually insert a trade signal."""
    # Create session
    resp = await client.post("/api/v1/sessions", json={
        "session_name": "Test Exec",
        "starting_balance": balance,
        "risk_tolerance": risk_tolerance,
    }, headers=headers)
    session_id = resp.json()["id"]

    # Insert a signal directly via the DB through the analyze-like mock
    # We'll use a lower-level approach: create signal via service
    from sqlalchemy.ext.asyncio import AsyncSession as AS
    from tests.conftest import test_session
    from app.models.trade_signal import TradeSignal

    async with test_session() as db:
        signal = TradeSignal(
            session_id=session_id,
            action=action,
            asset=asset,
            conviction=conviction,
            reasoning="Test reasoning for execution",
            risk_score=5,
            raw_prompt="test prompt",
            raw_response="test response",
            model_used="test-model",
        )
        db.add(signal)
        await db.commit()
        await db.refresh(signal)
        signal_id = signal.id

    return session_id, signal_id


async def _register_and_get_token(client: AsyncClient, username: str) -> str:
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpass123",
    })
    return resp.json()["access_token"]


# ── BUY Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_buy_basic():
    """Basic BUY creates a trade and position."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_buy_basic")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, signal_id = await _setup_session_and_signal(client, headers)

        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=15000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                from app.services.slippage import SlippageResult
                mock_slip.return_value = SlippageResult(execution_price_cents=15015, factor=0.001)
                resp = await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{signal_id}/execute",
                    headers=headers,
                )

    assert resp.status_code == 200
    data = resp.json()
    assert "trade" in data
    assert data["trade"]["side"] == "BUY"
    assert data["trade"]["asset"] == "AAPL"
    assert data["trade"]["quantity"] > 0
    assert "position" in data
    assert data["new_balance"] < 10000.0


@pytest.mark.asyncio
async def test_buy_updates_wapp():
    """Buying more shares updates WAPP correctly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_buy_wapp")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, signal_id1 = await _setup_session_and_signal(
            client, headers, balance=100000.0
        )

        # First BUY at $100
        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=10000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                from app.services.slippage import SlippageResult
                mock_slip.return_value = SlippageResult(execution_price_cents=10000, factor=0.0)
                resp1 = await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{signal_id1}/execute",
                    headers=headers,
                )

        assert resp1.status_code == 200
        position1 = resp1.json()["position"]

        # Create second signal for same asset
        from tests.conftest import test_session
        from app.models.trade_signal import TradeSignal
        async with test_session() as db:
            signal2 = TradeSignal(
                session_id=session_id, action="BUY", asset="AAPL",
                conviction=0.8, reasoning="Second buy", risk_score=5,
                raw_prompt="p", raw_response="r", model_used="test",
            )
            db.add(signal2)
            await db.commit()
            await db.refresh(signal2)
            signal_id2 = signal2.id

        # Second BUY at $200
        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=20000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                mock_slip.return_value = SlippageResult(execution_price_cents=20000, factor=0.0)
                resp2 = await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{signal_id2}/execute",
                    headers=headers,
                )

        assert resp2.status_code == 200
        position2 = resp2.json()["position"]
        # WAPP should be between $100 and $200
        assert position2["wapp"] >= 100.0
        assert position2["wapp"] <= 200.0
        assert position2["quantity"] > position1["quantity"]


@pytest.mark.asyncio
async def test_buy_insufficient_balance():
    """BUY with insufficient balance returns 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_buy_insuff")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, signal_id = await _setup_session_and_signal(
            client, headers, balance=1.0,  # $1.00
        )

        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=15000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                from app.services.slippage import SlippageResult
                mock_slip.return_value = SlippageResult(execution_price_cents=15000, factor=0.0)
                resp = await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{signal_id}/execute",
                    headers=headers,
                )

    assert resp.status_code == 400
    assert "Insufficient balance" in resp.json()["detail"]


# ── SELL Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sell_basic():
    """Basic SELL after a BUY succeeds."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_sell_basic")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, buy_signal_id = await _setup_session_and_signal(
            client, headers, balance=50000.0,
        )

        # BUY first
        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=10000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                from app.services.slippage import SlippageResult
                mock_slip.return_value = SlippageResult(execution_price_cents=10000, factor=0.0)
                await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{buy_signal_id}/execute",
                    headers=headers,
                )

        # Create SELL signal
        from tests.conftest import test_session
        from app.models.trade_signal import TradeSignal
        async with test_session() as db:
            sell_signal = TradeSignal(
                session_id=session_id, action="SELL", asset="AAPL",
                conviction=0.5, reasoning="Take profit", risk_score=3,
                raw_prompt="p", raw_response="r", model_used="test",
            )
            db.add(sell_signal)
            await db.commit()
            await db.refresh(sell_signal)
            sell_signal_id = sell_signal.id

        # SELL at higher price (profit)
        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=12000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                mock_slip.return_value = SlippageResult(execution_price_cents=12000, factor=0.0)
                resp = await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{sell_signal_id}/execute",
                    headers=headers,
                )

    assert resp.status_code == 200
    data = resp.json()
    assert data["trade"]["side"] == "SELL"
    assert data["trade"]["realized_pnl"] > 0  # Profit


@pytest.mark.asyncio
async def test_sell_no_position():
    """SELL without position returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_sell_nopos")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, signal_id = await _setup_session_and_signal(
            client, headers, action="SELL",
        )

        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=10000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                from app.services.slippage import SlippageResult
                mock_slip.return_value = SlippageResult(execution_price_cents=10000, factor=0.0)
                resp = await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{signal_id}/execute",
                    headers=headers,
                )

    assert resp.status_code == 404
    assert "No open position" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_sell_realized_pnl_negative():
    """Selling at a loss produces negative realized PnL."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_sell_loss")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, buy_signal_id = await _setup_session_and_signal(
            client, headers, balance=50000.0,
        )

        # BUY at $150
        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=15000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                from app.services.slippage import SlippageResult
                mock_slip.return_value = SlippageResult(execution_price_cents=15000, factor=0.0)
                await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{buy_signal_id}/execute",
                    headers=headers,
                )

        from tests.conftest import test_session
        from app.models.trade_signal import TradeSignal
        async with test_session() as db:
            sell_signal = TradeSignal(
                session_id=session_id, action="SELL", asset="AAPL",
                conviction=1.0, reasoning="Stop loss", risk_score=8,
                raw_prompt="p", raw_response="r", model_used="test",
            )
            db.add(sell_signal)
            await db.commit()
            await db.refresh(sell_signal)
            sell_signal_id = sell_signal.id

        # SELL at $100 (loss)
        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=10000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                mock_slip.return_value = SlippageResult(execution_price_cents=10000, factor=0.0)
                resp = await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{sell_signal_id}/execute",
                    headers=headers,
                )

    assert resp.status_code == 200
    assert resp.json()["trade"]["realized_pnl"] < 0


# ── HOLD Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_hold_marks_executed():
    """HOLD signal gets marked as executed with no trade."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_hold")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, signal_id = await _setup_session_and_signal(
            client, headers, action="HOLD", asset="CASH",
        )

        resp = await client.post(
            f"/api/v1/sessions/{session_id}/signals/{signal_id}/execute",
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "HOLD"
    assert data["action_taken"] == "executed"
    assert "trade" not in data


@pytest.mark.asyncio
async def test_hold_no_balance_change():
    """HOLD should not change the session balance."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_hold_bal")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, signal_id = await _setup_session_and_signal(
            client, headers, action="HOLD", asset="CASH", balance=5000.0,
        )

        await client.post(
            f"/api/v1/sessions/{session_id}/signals/{signal_id}/execute",
            headers=headers,
        )

        # Check balance unchanged
        resp = await client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        assert resp.json()["current_balance"] == 5000.0


# ── Skip Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_skip_marks_skipped():
    """Skip marks signal as skipped."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_skip")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, signal_id = await _setup_session_and_signal(client, headers)

        resp = await client.post(
            f"/api/v1/sessions/{session_id}/signals/{signal_id}/skip",
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["signal_id"] == signal_id
    assert data["action_taken"] == "skipped"


@pytest.mark.asyncio
async def test_already_executed_returns_409():
    """Executing an already-executed signal returns 409."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_409")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, signal_id = await _setup_session_and_signal(
            client, headers, action="HOLD", asset="CASH",
        )

        # Execute once
        await client.post(
            f"/api/v1/sessions/{session_id}/signals/{signal_id}/execute",
            headers=headers,
        )

        # Try again
        resp = await client.post(
            f"/api/v1/sessions/{session_id}/signals/{signal_id}/execute",
            headers=headers,
        )

    assert resp.status_code == 409


# ── Close Position Tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_position():
    """Closing a position sells all shares."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_close")
        headers = {"Authorization": f"Bearer {token}"}
        session_id, buy_signal_id = await _setup_session_and_signal(
            client, headers, balance=50000.0,
        )

        # BUY first
        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=10000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                from app.services.slippage import SlippageResult
                mock_slip.return_value = SlippageResult(execution_price_cents=10000, factor=0.0)
                buy_resp = await client.post(
                    f"/api/v1/sessions/{session_id}/signals/{buy_signal_id}/execute",
                    headers=headers,
                )

        position_id = buy_resp.json()["position"]["id"]

        # Close at same price
        with patch("app.services.execution.get_price_cents", new_callable=AsyncMock, return_value=10000):
            with patch("app.services.execution.apply_slippage") as mock_slip:
                mock_slip.return_value = SlippageResult(execution_price_cents=10000, factor=0.0)
                resp = await client.post(
                    f"/api/v1/sessions/{session_id}/positions/{position_id}/close",
                    headers=headers,
                )

    assert resp.status_code == 200
    data = resp.json()
    assert data["position"]["is_open"] is False
    assert data["position"]["quantity"] == 0


@pytest.mark.asyncio
async def test_close_nonexistent_position():
    """Closing a nonexistent position returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_get_token(client, "exec_close_404")
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post("/api/v1/sessions", json={
            "session_name": "Close 404",
            "starting_balance": 1000.0,
        }, headers=headers)
        session_id = resp.json()["id"]

        resp = await client.post(
            f"/api/v1/sessions/{session_id}/positions/99999/close",
            headers=headers,
        )

    assert resp.status_code == 404
