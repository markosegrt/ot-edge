from datetime import datetime

from edge.domain.models.security_alert import SecurityAlert
from edge.domain.enums.severity import Severity
from edge.domain.enums.event_type import EventType
from edge.domain.enums.protocol import Protocol
from edge.domain.repositories.security_event_repository import SecurityEventRepository
from edge.db.base import SessionLocal
from edge.db.orm.security_event import SecurityEventORM


class SqlSecurityEventRepository(SecurityEventRepository):
    def save(self, alert: SecurityAlert) -> None:
        with SessionLocal() as session:
            row = self._to_orm(alert)
            session.add(row)
            session.commit()

    def get_all(self) -> list[SecurityAlert]:
        with SessionLocal() as session:
            rows = session.query(SecurityEventORM).all()
            return [self._to_domain(row) for row in rows]

    def _to_orm(self, alert: SecurityAlert) -> SecurityEventORM:
        return SecurityEventORM(
            timestamp=alert.timestamp,
            event_type=alert.event_type.value,
            severity=alert.severity.value,
            source=alert.source,
            destination=alert.destination,
            protocol=alert.protocol.value,
            rule_id=alert.rule_id,
            correlated=alert.correlated,
            extra=alert.extra,
        )

    def _to_domain(self, row: SecurityEventORM) -> SecurityAlert:
        return SecurityAlert(
            timestamp=row.timestamp,
            rule_id=row.rule_id,
            severity=Severity(row.severity),
            event_type=EventType(row.event_type),
            source=row.source,
            destination=row.destination,
            device=row.destination,
            protocol=Protocol(row.protocol),
            correlated=row.correlated,
            extra=row.extra or {},
        )

    def find_recent_duplicate_id(
        self, rule_id: str, source: str, destination: str, since: datetime
    ) -> int | None:
        with SessionLocal() as session:
            row = (
                session.query(SecurityEventORM)
                .filter(SecurityEventORM.rule_id == rule_id)
                .filter(SecurityEventORM.source == source)
                .filter(SecurityEventORM.destination == destination)
                .filter(SecurityEventORM.timestamp >= since)
                .order_by(SecurityEventORM.timestamp.desc())
                .first()
            )
            return row.id if row else None

    def increment_occurrence(self, alert_id: int) -> None:
        with SessionLocal() as session:
            row = session.query(SecurityEventORM).filter(SecurityEventORM.id == alert_id).first()
            if row:
                row.occurrence_count += 1
                session.commit()