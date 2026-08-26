from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from edge.db.base import Base


class SecurityEventORM(Base):
    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(45), nullable=False)
    destination: Mapped[str] = mapped_column(String(45), nullable=False)
    device_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("devices.id"), nullable=True)
    flow_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("network_flows.id"), nullable=True)
    incident_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("incidents.id"), nullable=True)
    protocol: Mapped[str] = mapped_column(String(20), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    correlated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)