from pydantic import BaseModel

from app.schemas.position import PositionResponse
from app.schemas.trade import TradeResponse


class ExecuteSignalResponse(BaseModel):
    trade: TradeResponse
    position: PositionResponse
    new_balance: float


class HoldExecuteResponse(BaseModel):
    signal_id: int
    action: str
    action_taken: str


class SkipSignalResponse(BaseModel):
    signal_id: int
    action_taken: str


class ClosePositionResponse(BaseModel):
    trade: TradeResponse
    position: PositionResponse
    new_balance: float
