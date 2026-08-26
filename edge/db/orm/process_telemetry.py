from datetime import datetime

from sqlalchemy import BigInteger, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from edge.db.base import Base


class ProcessTelemetryORM(Base):
    __tablename__ = "process_telemetry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    device_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("devices.id"), nullable=True)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quality: Mapped[str] = mapped_column(String(20), nullable=False, default="GOOD")