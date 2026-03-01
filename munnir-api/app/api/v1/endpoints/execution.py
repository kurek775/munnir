from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.execution import (
    ClosePositionResponse,
    ExecuteSignalResponse,
    HoldExecuteResponse,
    SkipSignalResponse,
)
from app.schemas.position import PositionResponse
from app.schemas.trade import TradeResponse
from app.services.execution import (
    close_position,
    execute_signal,
    get_session_positions,
    get_session_trades,
    skip_signal,
)

router = APIRouter(prefix="/sessions")


@router.post(
    "/{session_id}/signals/{signal_id}/execute",
    response_model=ExecuteSignalResponse | HoldExecuteResponse,
)
async def execute(
    session_id: int,
    signal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await execute_signal(session_id, signal_id, current_user, db)
    if result.get("type") == "hold":
        return HoldExecuteResponse(
            signal_id=result["signal_id"],
            action=result["action"],
            action_taken=result["action_taken"],
        )
    return ExecuteSignalResponse(
        trade=TradeResponse.model_validate(result["trade"]),
        position=PositionResponse.model_validate(result["position"]),
        new_balance=result["new_balance"],
    )


@router.post(
    "/{session_id}/signals/{signal_id}/skip",
    response_model=SkipSignalResponse,
)
async def skip(
    session_id: int,
    signal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await skip_signal(session_id, signal_id, current_user, db)
    return SkipSignalResponse(**result)


@router.get("/{session_id}/trades", response_model=list[TradeResponse])
async def trades(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_session_trades(session_id, current_user, db)


@router.get("/{session_id}/positions", response_model=list[PositionResponse])
async def positions(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_session_positions(session_id, current_user, db)


@router.post(
    "/{session_id}/positions/{position_id}/close",
    response_model=ClosePositionResponse,
)
async def close(
    session_id: int,
    position_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await close_position(session_id, position_id, current_user, db)
    return ClosePositionResponse(
        trade=TradeResponse.model_validate(result["trade"]),
        position=PositionResponse.model_validate(result["position"]),
        new_balance=result["new_balance"],
    )
