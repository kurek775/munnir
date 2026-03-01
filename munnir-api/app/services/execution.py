"""Execution service — orchestrates trade execution, position tracking, and P&L."""

import logging
import math

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.position import Position
from app.models.trade import Trade
from app.models.trade_signal import TradeSignal
from app.models.trading_session import TradingSession
from app.models.user import User
from app.services.engine import RiskTolerance, adjust_risk
from app.services.price_feed import get_price_cents
from app.services.slippage import apply_slippage

logger = logging.getLogger(__name__)


async def _get_session(session_id: int, user: User, db: AsyncSession) -> TradingSession:
    result = await db.execute(
        select(TradingSession).where(
            TradingSession.id == session_id,
            TradingSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


async def _get_signal(signal_id: int, session_id: int, db: AsyncSession) -> TradeSignal:
    result = await db.execute(
        select(TradeSignal).where(
            TradeSignal.id == signal_id,
            TradeSignal.session_id == session_id,
        )
    )
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")
    return signal


async def _get_or_create_position(
    session_id: int, asset: str, db: AsyncSession
) -> Position:
    result = await db.execute(
        select(Position).where(
            Position.session_id == session_id,
            Position.asset == asset,
            Position.is_open == True,  # noqa: E712
        )
    )
    position = result.scalar_one_or_none()
    if position:
        return position

    position = Position(session_id=session_id, asset=asset)
    db.add(position)
    await db.flush()
    return position


def _tolerance_enum(risk_str: str) -> RiskTolerance:
    return RiskTolerance(risk_str.lower())


async def execute_signal(
    session_id: int, signal_id: int, user: User, db: AsyncSession
) -> dict:
    """Execute a trade signal (BUY/SELL/HOLD)."""
    session = await _get_session(session_id, user, db)
    signal = await _get_signal(signal_id, session_id, db)

    if signal.action_taken != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Signal already {signal.action_taken}",
        )

    # HOLD — mark executed, no trade
    if signal.action == "HOLD":
        signal.action_taken = "executed"
        await db.commit()
        await db.refresh(signal)
        return {
            "type": "hold",
            "signal_id": signal.id,
            "action": signal.action,
            "action_taken": signal.action_taken,
        }

    fee_cents = settings.TRADE_FEE_CENTS
    tolerance = _tolerance_enum(session.risk_tolerance)
    market_price_cents = await get_price_cents(signal.asset)
    slippage_result = apply_slippage(
        market_price_cents, signal.action, session.risk_tolerance, settings.SLIPPAGE_ENABLED
    )
    exec_price = slippage_result.execution_price_cents

    if signal.action == "BUY":
        return await _execute_buy(
            session, signal, market_price_cents, exec_price,
            slippage_result.factor, fee_cents, tolerance, db,
        )
    elif signal.action == "SELL":
        return await _execute_sell(
            session, signal, market_price_cents, exec_price,
            slippage_result.factor, fee_cents, db,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {signal.action}",
        )


async def execute_signal_internal(
    session_id: int, signal_id: int, db: AsyncSession
) -> dict | None:
    """Execute a trade signal without user ownership check (for auto-pilot).

    HOLD signals are auto-skipped. On execution failure, the signal is auto-skipped
    to prevent perpetually pending signals.
    """
    result = await db.execute(
        select(TradingSession).where(TradingSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        logger.warning("execute_signal_internal: session %d not found", session_id)
        return None

    signal = await _get_signal(signal_id, session_id, db)

    if signal.action_taken != "pending":
        return None

    # HOLD → auto-skip
    if signal.action == "HOLD":
        signal.action_taken = "skipped"
        await db.commit()
        return {"type": "hold", "signal_id": signal.id, "action_taken": "skipped"}

    fee_cents = settings.TRADE_FEE_CENTS
    tolerance = _tolerance_enum(session.risk_tolerance)

    try:
        market_price_cents = await get_price_cents(signal.asset)
        slippage_result = apply_slippage(
            market_price_cents, signal.action, session.risk_tolerance, settings.SLIPPAGE_ENABLED
        )
        exec_price = slippage_result.execution_price_cents

        if signal.action == "BUY":
            return await _execute_buy(
                session, signal, market_price_cents, exec_price,
                slippage_result.factor, fee_cents, tolerance, db,
            )
        elif signal.action == "SELL":
            return await _execute_sell(
                session, signal, market_price_cents, exec_price,
                slippage_result.factor, fee_cents, db,
            )
    except HTTPException as exc:
        logger.warning(
            "Auto-pilot execution failed for signal %d: %s — auto-skipping",
            signal_id, exc.detail,
        )
        signal.action_taken = "skipped"
        await db.commit()
        return {"type": "skipped", "signal_id": signal.id, "reason": exc.detail}

    return None


async def _execute_buy(
    session: TradingSession,
    signal: TradeSignal,
    market_price_cents: int,
    exec_price: int,
    slippage_factor: float,
    fee_cents: int,
    tolerance: RiskTolerance,
    db: AsyncSession,
) -> dict:
    """Execute a BUY signal."""
    adjusted_risk = adjust_risk(
        session.current_balance, session.starting_balance, tolerance
    )
    conviction = max(0.0, min(1.0, signal.conviction))
    risk_amount = session.current_balance * adjusted_risk * conviction

    if exec_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid execution price",
        )

    shares = math.floor(risk_amount / exec_price)

    # Auto-reduce: ensure we can afford shares + fee
    while shares > 0 and (shares * exec_price + fee_cents) > session.current_balance:
        shares -= 1

    if shares <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance for even 1 share",
        )

    total_cost = shares * exec_price + fee_cents
    position = await _get_or_create_position(session.session_id if hasattr(session, 'session_id') else session.id, signal.asset, db)

    # Update position WAPP
    position.total_cost_basis_cents += shares * exec_price
    position.quantity += shares
    position.wapp_cents = position.total_cost_basis_cents // position.quantity if position.quantity > 0 else 0

    # Deduct from balance
    session.current_balance -= total_cost

    trade = Trade(
        session_id=session.id,
        signal_id=signal.id,
        position_id=position.id,
        side="BUY",
        asset=signal.asset,
        quantity=shares,
        market_price_cents=market_price_cents,
        execution_price_cents=exec_price,
        slippage_factor=slippage_factor,
        fee_cents=fee_cents,
        total_cost_cents=total_cost,
    )
    db.add(trade)
    signal.action_taken = "executed"

    await db.commit()
    await db.refresh(trade)
    await db.refresh(position)
    await db.refresh(session)

    return {
        "type": "trade",
        "trade": trade,
        "position": position,
        "new_balance": session.current_balance / 100,
    }


async def _execute_sell(
    session: TradingSession,
    signal: TradeSignal,
    market_price_cents: int,
    exec_price: int,
    slippage_factor: float,
    fee_cents: int,
    db: AsyncSession,
) -> dict:
    """Execute a SELL signal."""
    position = await _find_open_position(session.id, signal.asset, db)

    conviction = max(0.0, min(1.0, signal.conviction))
    sell_qty = math.floor(position.quantity * conviction)
    if sell_qty <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sell quantity is zero",
        )

    realized_pnl = (exec_price - position.wapp_cents) * sell_qty
    proceeds = sell_qty * exec_price - fee_cents
    total_cost = sell_qty * exec_price - fee_cents  # net proceeds (negative "cost")

    # Update position
    position.quantity -= sell_qty
    position.realized_pnl_cents += realized_pnl
    if position.quantity <= 0:
        position.quantity = 0
        position.is_open = False
        from sqlalchemy import func
        position.closed_at = func.now()

    # Credit balance
    session.current_balance += proceeds

    trade = Trade(
        session_id=session.id,
        signal_id=signal.id,
        position_id=position.id,
        side="SELL",
        asset=signal.asset,
        quantity=sell_qty,
        market_price_cents=market_price_cents,
        execution_price_cents=exec_price,
        slippage_factor=slippage_factor,
        fee_cents=fee_cents,
        total_cost_cents=total_cost,
        realized_pnl_cents=realized_pnl,
    )
    db.add(trade)
    signal.action_taken = "executed"

    await db.commit()
    await db.refresh(trade)
    await db.refresh(position)
    await db.refresh(session)

    return {
        "type": "trade",
        "trade": trade,
        "position": position,
        "new_balance": session.current_balance / 100,
    }


async def _find_open_position(
    session_id: int, asset: str, db: AsyncSession
) -> Position:
    result = await db.execute(
        select(Position).where(
            Position.session_id == session_id,
            Position.asset == asset,
            Position.is_open == True,  # noqa: E712
        )
    )
    position = result.scalar_one_or_none()
    if not position or position.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No open position for {asset}",
        )
    return position


async def skip_signal(
    session_id: int, signal_id: int, user: User, db: AsyncSession
) -> dict:
    """Mark a signal as skipped."""
    await _get_session(session_id, user, db)
    signal = await _get_signal(signal_id, session_id, db)

    if signal.action_taken != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Signal already {signal.action_taken}",
        )

    signal.action_taken = "skipped"
    await db.commit()
    await db.refresh(signal)

    return {"signal_id": signal.id, "action_taken": signal.action_taken}


async def close_position(
    session_id: int, position_id: int, user: User, db: AsyncSession
) -> dict:
    """Close an entire position at market price."""
    session = await _get_session(session_id, user, db)

    result = await db.execute(
        select(Position).where(
            Position.id == position_id,
            Position.session_id == session_id,
            Position.is_open == True,  # noqa: E712
        )
    )
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found or already closed",
        )

    fee_cents = settings.TRADE_FEE_CENTS
    market_price_cents = await get_price_cents(position.asset)
    slippage_result = apply_slippage(
        market_price_cents, "SELL", session.risk_tolerance, settings.SLIPPAGE_ENABLED
    )
    exec_price = slippage_result.execution_price_cents

    sell_qty = position.quantity
    realized_pnl = (exec_price - position.wapp_cents) * sell_qty
    proceeds = sell_qty * exec_price - fee_cents

    position.quantity = 0
    position.is_open = False
    position.realized_pnl_cents += realized_pnl
    from sqlalchemy import func
    position.closed_at = func.now()

    session.current_balance += proceeds

    trade = Trade(
        session_id=session.id,
        signal_id=None,
        position_id=position.id,
        side="SELL",
        asset=position.asset,
        quantity=sell_qty,
        market_price_cents=market_price_cents,
        execution_price_cents=exec_price,
        slippage_factor=slippage_result.factor,
        fee_cents=fee_cents,
        total_cost_cents=proceeds,
        realized_pnl_cents=realized_pnl,
    )
    db.add(trade)

    await db.commit()
    await db.refresh(trade)
    await db.refresh(position)
    await db.refresh(session)

    return {
        "type": "close",
        "trade": trade,
        "position": position,
        "new_balance": session.current_balance / 100,
    }


async def get_session_trades(
    session_id: int, user: User, db: AsyncSession
) -> list[Trade]:
    await _get_session(session_id, user, db)
    result = await db.execute(
        select(Trade)
        .where(Trade.session_id == session_id)
        .order_by(Trade.created_at.desc())
    )
    return list(result.scalars().all())


async def get_session_positions(
    session_id: int, user: User, db: AsyncSession
) -> list[Position]:
    await _get_session(session_id, user, db)
    result = await db.execute(
        select(Position)
        .where(Position.session_id == session_id)
        .order_by(Position.opened_at.desc())
    )
    return list(result.scalars().all())
