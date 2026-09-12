from datetime import datetime, timezone

from edge.domain.models.correlation import Correlation
from edge.db.base import SessionLocal
from edge.db.orm.correlation import CorrelationORM


class SqlCorrelationRepository:
    def save(self, correlation: Correlation) -> int:
        with SessionLocal() as session:
            row = CorrelationORM(
                event_id=correlation.event_id,
                pattern=correlation.pattern,
                base_severity=correlation.base_severity,
                final_severity=correlation.final_severity,
                network_summary=correlation.network_summary,
                process_summary=correlation.process_summary,
                link_summary=correlation.link_summary,
                created_at=correlation.created_at or datetime.now(timezone.utc),
            )
            session.add(row)
            session.commit()
            return row.id

    def get_by_event_id(self, event_id: int) -> Correlation | None:
        with SessionLocal() as session:
            row = (
                session.query(CorrelationORM)
                .filter(CorrelationORM.event_id == event_id)
                .first()
            )
            if row is None:
                return None
            return Correlation(
                id=row.id,
                event_id=row.event_id,
                pattern=row.pattern,
                base_severity=row.base_severity,
                final_severity=row.final_severity,
                network_summary=row.network_summary,
                process_summary=row.process_summary,
                link_summary=row.link_summary,
                created_at=row.created_at,
            )