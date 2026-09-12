from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from edge.db.base import Base


class CorrelationORM(Base):
    __tablename__ = "correlations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("security_events.id", ondelete="CASCADE"), nullable=False
    )
    pattern: Mapped[str] = mapped_column(String(40), nullable=False)
    base_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    final_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    network_summary: Mapped[str | None] = mapped_column(String(400), nullable=True)
    process_summary: Mapped[str | None] = mapped_column(String(400), nullable=True)
    link_summary: Mapped[str | None] = mapped_column(String(400), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)