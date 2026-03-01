"""add news_articles and trade_signals tables

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-01 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_news_articles_content_hash", "news_articles", ["content_hash"])

    op.create_table(
        "trade_signals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("asset", sa.String(), nullable=False),
        sa.Column("conviction", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("raw_prompt", sa.Text(), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column(
            "action_taken",
            sa.String(),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["trading_sessions.id"]),
        sa.ForeignKeyConstraint(["article_id"], ["news_articles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trade_signals_session_id", "trade_signals", ["session_id"])
    op.create_index("ix_trade_signals_article_id", "trade_signals", ["article_id"])


def downgrade() -> None:
    op.drop_index("ix_trade_signals_article_id", table_name="trade_signals")
    op.drop_index("ix_trade_signals_session_id", table_name="trade_signals")
    op.drop_table("trade_signals")
    op.drop_index("ix_news_articles_content_hash", table_name="news_articles")
    op.drop_table("news_articles")
