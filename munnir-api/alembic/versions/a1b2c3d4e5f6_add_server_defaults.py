"""add server_default values for user and session columns

Revision ID: a1b2c3d4e5f6
Revises: 6c8348f00e17
Create Date: 2026-03-01 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6c8348f00e17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "preferred_theme",
            server_default=sa.text("'dark'"),
        )
        batch_op.alter_column(
            "preferred_language",
            server_default=sa.text("'en'"),
        )

    with op.batch_alter_table("trading_sessions") as batch_op:
        batch_op.alter_column(
            "risk_tolerance",
            server_default=sa.text("'medium'"),
        )
        batch_op.alter_column(
            "is_active",
            server_default=sa.text("1"),
        )


def downgrade() -> None:
    with op.batch_alter_table("trading_sessions") as batch_op:
        batch_op.alter_column("is_active", server_default=None)
        batch_op.alter_column("risk_tolerance", server_default=None)

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("preferred_language", server_default=None)
        batch_op.alter_column("preferred_theme", server_default=None)
