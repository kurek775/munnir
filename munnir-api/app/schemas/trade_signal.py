from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TradeSignalLLM(BaseModel):
    """Structured output schema that Gemini must produce."""

    action: Literal["BUY", "SELL", "HOLD"]
    asset: str = Field(pattern=r"^[A-Z]{1,5}$")
    conviction: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=10, max_length=500)
    risk_score: int = Field(ge=1, le=10)


class TradeSignalResponse(BaseModel):
    id: int
    session_id: int
    article_id: int | None
    action: str
    asset: str
    conviction: float
    reasoning: str
    risk_score: int
    model_used: str
    action_taken: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyzeResponse(BaseModel):
    signal: TradeSignalResponse
    articles_used: int
