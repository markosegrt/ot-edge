from datetime import datetime

from pydantic import BaseModel

from edge.db.repositories.security_event_repository import SqlSecurityEventRepository


class AlertResponse(BaseModel):
    id: int
    timestamp: datetime
    rule_id: str | None
    severity: str
    source: str
    destination: str
    protocol: str
    correlated: bool
    occurrence_count: int


class AlarmsController:
    def __init__(self):
        self.alert_repository = SqlSecurityEventRepository()

    def list_alarms(self) -> list[AlertResponse]:
        rows = self.alert_repository.get_all_rows()
        return [
            AlertResponse(
                id=r.id,
                timestamp=r.timestamp,
                rule_id=r.rule_id,
                severity=r.severity,
                source=r.source,
                destination=r.destination,
                protocol=r.protocol,
                correlated=r.correlated,
                occurrence_count=r.occurrence_count,
            )
            for r in rows
        ]