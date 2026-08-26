from datetime import datetime

from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from edge.db.base import Base


class RuleStateORM(Base):
    __tablename__ = "rule_state"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_triggered: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trigger_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)