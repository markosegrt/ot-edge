from datetime import datetime

from edge.domain.models.incident import Incident
from edge.domain.enums.severity import Severity
from edge.domain.enums.incident_status import IncidentStatus
from edge.domain.repositories.incident_repository import IncidentRepository
from edge.db.base import SessionLocal
from edge.db.orm.incident import IncidentORM


class SqlIncidentRepository(IncidentRepository):
    def save(self, incident: Incident) -> int:
        with SessionLocal() as session:
            row = IncidentORM(
                severity=incident.severity.value,
                status=incident.status.value,
                opened_at=incident.opened_at,
                closed_at=incident.closed_at,
                alarm_count=incident.alarm_count,
            )
            session.add(row)
            session.commit()
            return row.id

    def get_open_for_device(self, device: str, since: datetime) -> Incident | None:
        with SessionLocal() as session:
            row = (
                session.query(IncidentORM)
                .filter(IncidentORM.status == IncidentStatus.OPEN.value)
                .filter(IncidentORM.opened_at >= since)
                .order_by(IncidentORM.opened_at.desc())
                .first()
            )
            return self._to_domain(row) if row else None

    def increment_alarm_count(self, incident_id: int) -> None:
        with SessionLocal() as session:
            row = session.query(IncidentORM).filter(IncidentORM.id == incident_id).first()
            if row:
                row.alarm_count += 1
                session.commit()

    def _to_domain(self, row: IncidentORM) -> Incident:
        return Incident(
            device="",
            severity=Severity(row.severity),
            status=IncidentStatus(row.status),
            opened_at=row.opened_at,
            closed_at=row.closed_at,
            alarm_count=row.alarm_count,
        )