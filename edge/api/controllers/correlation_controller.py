from datetime import datetime, timedelta

from pydantic import BaseModel

from edge.db.repositories.security_event_repository import SqlSecurityEventRepository
from edge.db.repositories.telemetry_repository import SqlTelemetryRepository

WINDOW_SECONDS = 5


class TelemetryPointResponse(BaseModel):
    timestamp: datetime
    tag: str
    value: float


class CorrelationContextResponse(BaseModel):
    alert_id: int
    alert_timestamp: datetime
    rule_id: str | None
    severity: str
    source: str
    destination: str
    correlated: bool
    window_start: datetime
    window_end: datetime
    telemetry: list[TelemetryPointResponse]


class CorrelationController:
    def __init__(self):
        self.alert_repository = SqlSecurityEventRepository()
        self.telemetry_repository = SqlTelemetryRepository()

    def get_context(self, alert_id: int) -> CorrelationContextResponse | None:
        alert = self.alert_repository.get_row_by_id(alert_id)
        if alert is None:
            return None

        window = timedelta(seconds=WINDOW_SECONDS)
        start = alert.timestamp - window
        end = alert.timestamp + window

        telemetry = self.telemetry_repository.get_between(start, end)

        return CorrelationContextResponse(
            alert_id=alert.id,
            alert_timestamp=alert.timestamp,
            rule_id=alert.rule_id,
            severity=alert.severity,
            source=alert.source,
            destination=alert.destination,
            correlated=alert.correlated,
            window_start=start,
            window_end=end,
            telemetry=[
                TelemetryPointResponse(timestamp=t.timestamp, tag=t.tag, value=t.value)
                for t in telemetry
            ],
        )