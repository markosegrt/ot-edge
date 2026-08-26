from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from edge.db.base import Base


class DeviceORM(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    mac: Mapped[str | None] = mapped_column(String(17), nullable=True)
    device_type: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEW")
    vendor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)