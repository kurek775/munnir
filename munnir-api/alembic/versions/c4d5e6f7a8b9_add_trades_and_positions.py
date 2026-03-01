"""add trades and positions

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-03-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Positions first (FK target for trades)
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("asset", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wapp_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cost_basis_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("realized_pnl_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_open", sa.Boolean(), nullable=True, server_default="1"),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["session_id"], ["trading_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_positions_session_id", "positions", ["session_id"])

    # Trades table
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("signal_id", sa.Integer(), nullable=True),
        sa.Column("position_id", sa.Integer(), nullable=True),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("asset", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("market_price_cents", sa.Integer(), nullable=False),
        sa.Column("execution_price_cents", sa.Integer(), nullable=False),
        sa.Column("slippage_factor", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fee_cents", sa.Integer(), nullable=False),
        sa.Column("total_cost_cents", sa.Integer(), nullable=False),
        sa.Column("realized_pnl_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["session_id"], ["trading_sessions.id"]),
        sa.ForeignKeyConstraint(["signal_id"], ["trade_signals.id"]),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trades_session_id", "trades", ["session_id"])
    op.create_index("ix_trades_signal_id", "trades", ["signal_id"])
    op.create_index("ix_trades_position_id", "trades", ["position_id"])


def downgrade() -> None:
    op.drop_table("trades")
    op.drop_table("positions")
