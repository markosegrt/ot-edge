"""baseline_devices table with seed

Revision ID: dd4222c954fa
Revises: 7e50057572e6
Create Date: 2026-09-11 00:07:32.303878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd4222c954fa'
down_revision: Union[str, None] = '7e50057572e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "baseline_devices",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("ip", sa.String(length=45), nullable=False),
        sa.Column("device_type", sa.String(length=20), nullable=False, server_default="UNKNOWN"),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("trusted", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_write", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("ip", name="uq_baseline_devices_ip"),
    )

    # Pocetni sadrzaj: 4 poznata uredjaja iz lab-a.
    # KLJUCNO: samo SCADA (.30) sme da pise u PLC (can_write=True).
    # PLC-ovi i HMI: can_write=False. Ovo je osnova lanca HMI->SCADA->PLC:
    # svaki upis u PLC koji NIJE od SCADA-e okida RULE-007.
    baseline_table = sa.table(
        "baseline_devices",
        sa.column("ip", sa.String),
        sa.column("device_type", sa.String),
        sa.column("name", sa.String),
        sa.column("trusted", sa.Boolean),
        sa.column("can_write", sa.Boolean),
    )
    op.bulk_insert(
        baseline_table,
        [
            {"ip": "192.168.10.10", "device_type": "PLC", "name": "Glavni PLC", "trusted": True, "can_write": False},
            {"ip": "192.168.10.11", "device_type": "PLC", "name": "PLC pritiska", "trusted": True, "can_write": False},
            {"ip": "192.168.10.20", "device_type": "HMI", "name": "Operaterski HMI", "trusted": True, "can_write": False},
            {"ip": "192.168.10.30", "device_type": "SCADA", "name": "SCADA stanica", "trusted": True, "can_write": True},
        ],
    )


def downgrade() -> None:
    op.drop_table("baseline_devices")