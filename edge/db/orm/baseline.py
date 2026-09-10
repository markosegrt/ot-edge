from sqlalchemy import BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from edge.db.base import Base


class BaselineDeviceORM(Base):
    __tablename__ = "baseline_devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    device_type: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    trusted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    can_write: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)