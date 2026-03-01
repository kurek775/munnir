from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PositionResponse(BaseModel):
    id: int
    session_id: int
    asset: str
    quantity: int
    wapp: float = Field(validation_alias="wapp_cents")
    total_cost_basis: float = Field(validation_alias="total_cost_basis_cents")
    realized_pnl: float = Field(validation_alias="realized_pnl_cents")
    is_open: bool
    opened_at: datetime
    closed_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator("wapp", "total_cost_basis", "realized_pnl", mode="before")
    @classmethod
    def cents_to_dollars(cls, v: int) -> float:
        return v / 100
