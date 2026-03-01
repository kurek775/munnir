from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TradeResponse(BaseModel):
    id: int
    session_id: int
    signal_id: int | None
    position_id: int | None
    side: str
    asset: str
    quantity: int
    market_price: float = Field(validation_alias="market_price_cents")
    execution_price: float = Field(validation_alias="execution_price_cents")
    slippage_factor: float
    fee: float = Field(validation_alias="fee_cents")
    total_cost: float = Field(validation_alias="total_cost_cents")
    realized_pnl: float = Field(validation_alias="realized_pnl_cents")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator(
        "market_price", "execution_price", "fee", "total_cost", "realized_pnl",
        mode="before",
    )
    @classmethod
    def cents_to_dollars(cls, v: int) -> float:
        return v / 100
