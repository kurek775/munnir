"""Session service — CRUD logic for trading sessions."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trading_session import TradingSession
from app.models.user import User
from app.schemas.trading_session import SessionCreate, SessionUpdate


async def get_user_session(
    session_id: int, user: User, db: AsyncSession
) -> TradingSession:
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


async def list_user_sessions(user: User, db: AsyncSession) -> list[TradingSession]:
    result = await db.execute(
        select(TradingSession).where(TradingSession.user_id == user.id)
    )
    return list(result.scalars().all())


async def create_trading_session(
    data: SessionCreate, user: User, db: AsyncSession
) -> TradingSession:
    balance_cents = int(data.starting_balance * 100)
    session = TradingSession(
        user_id=user.id,
        session_name=data.session_name,
        starting_balance=balance_cents,
        current_balance=balance_cents,
        risk_tolerance=data.risk_tolerance,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def update_trading_session(
    session_id: int, data: SessionUpdate, user: User, db: AsyncSession
) -> TradingSession:
    session = await get_user_session(session_id, user, db)

    if data.session_name is not None:
        session.session_name = data.session_name
    if data.risk_tolerance is not None:
        session.risk_tolerance = data.risk_tolerance
    if data.is_active is not None:
        session.is_active = data.is_active
    if data.auto_pilot is not None:
        session.auto_pilot = data.auto_pilot
    if data.auto_pilot_interval_minutes is not None:
        session.auto_pilot_interval_minutes = data.auto_pilot_interval_minutes

    await db.commit()
    await db.refresh(session)
    return session


async def delete_trading_session(
    session_id: int, user: User, db: AsyncSession
) -> None:
    session = await get_user_session(session_id, user, db)
    await db.delete(session)
    await db.commit()
