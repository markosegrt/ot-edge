"""add correlation table

Revision ID: 58ab26640427
Revises: 0d2c05ee5a3d
Create Date: 2026-09-11 22:55:10.014085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58ab26640427'
down_revision: Union[str, None] = '0d2c05ee5a3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "correlations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("pattern", sa.String(length=40), nullable=False),
        sa.Column("base_severity", sa.String(length=20), nullable=False),
        sa.Column("final_severity", sa.String(length=20), nullable=False),
        sa.Column("network_summary", sa.String(length=400), nullable=True),
        sa.Column("process_summary", sa.String(length=400), nullable=True),
        sa.Column("link_summary", sa.String(length=400), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"], ["security_events.id"],
            name="fk_correlations_event", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_correlations_event_id", "correlations", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_correlations_event_id", table_name="correlations")
    op.drop_table("correlations")