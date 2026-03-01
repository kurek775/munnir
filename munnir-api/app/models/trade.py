from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trading_sessions.id"), index=True, nullable=False
    )
    signal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("trade_signals.id"), index=True, nullable=True
    )
    position_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("positions.id"), index=True, nullable=True
    )
    side: Mapped[str] = mapped_column(String, nullable=False)
    asset: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    market_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    slippage_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fee_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cost_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    realized_pnl_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session = relationship("TradingSession", back_populates="trades")
    signal = relationship("TradeSignal", back_populates="trade")
    position = relationship("Position", back_populates="trades")
