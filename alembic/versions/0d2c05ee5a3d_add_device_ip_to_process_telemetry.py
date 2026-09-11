"""add device_ip to process_telemetry

Revision ID: 0d2c05ee5a3d
Revises: dd4222c954fa
Create Date: 2026-09-11 22:01:03.946728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d2c05ee5a3d'
down_revision: Union[str, None] = 'dd4222c954fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "process_telemetry",
        sa.Column("device_ip", sa.String(length=45), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("process_telemetry", "device_ip")