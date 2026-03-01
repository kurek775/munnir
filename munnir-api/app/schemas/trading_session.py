from datetime import datetime

from pydantic import BaseModel, field_validator


class SessionCreate(BaseModel):
    session_name: str
    starting_balance: float
    risk_tolerance: str = "medium"

    @field_validator("risk_tolerance")
    @classmethod
    def validate_risk(cls, v: str) -> str:
        if v not in ("low", "medium", "high"):
            raise ValueError("risk_tolerance must be low, medium, or high")
        return v


class SessionUpdate(BaseModel):
    session_name: str | None = None
    risk_tolerance: str | None = None
    is_active: bool | None = None
    auto_pilot: bool | None = None

    @field_validator("risk_tolerance")
    @classmethod
    def validate_risk(cls, v: str | None) -> str | None:
        if v is not None and v not in ("low", "medium", "high"):
            raise ValueError("risk_tolerance must be low, medium, or high")
        return v


class SessionResponse(BaseModel):
    id: int
    session_name: str
    starting_balance: float
    current_balance: float
    risk_tolerance: str
    is_active: bool
    auto_pilot: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("starting_balance", "current_balance", mode="before")
    @classmethod
    def cents_to_dollars(cls, v: int) -> float:
        return v / 100
