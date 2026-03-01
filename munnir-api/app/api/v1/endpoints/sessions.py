from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.trading_session import TradingSession
from app.models.user import User
from app.schemas.trading_session import SessionCreate, SessionResponse, SessionUpdate

router = APIRouter(prefix="/sessions")


async def _get_user_session(
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


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    balance_cents = int(data.starting_balance * 100)
    session = TradingSession(
        user_id=current_user.id,
        session_name=data.session_name,
        starting_balance=balance_cents,
        current_balance=balance_cents,
        risk_tolerance=data.risk_tolerance,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TradingSession).where(TradingSession.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_user_session(session_id, current_user, db)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    data: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_user_session(session_id, current_user, db)

    if data.session_name is not None:
        session.session_name = data.session_name
    if data.risk_tolerance is not None:
        session.risk_tolerance = data.risk_tolerance
    if data.is_active is not None:
        session.is_active = data.is_active

    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_user_session(session_id, current_user, db)
    await db.delete(session)
    await db.commit()
