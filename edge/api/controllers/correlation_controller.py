from datetime import datetime, timedelta

from pydantic import BaseModel

from edge.db.repositories.security_event_repository import SqlSecurityEventRepository
from edge.db.repositories.telemetry_repository import SqlTelemetryRepository
from edge.db.repositories.correlation_repository import SqlCorrelationRepository

WINDOW_SECONDS = 5
LOOKAHEAD_SECONDS = 15


class TelemetryPointResponse(BaseModel):
    timestamp: datetime
    tag: str
    value: float


class CorrelationDetail(BaseModel):
    pattern: str
    base_severity: str
    final_severity: str
    network_summary: str | None
    process_summary: str | None
    link_summary: str | None


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
    correlation: CorrelationDetail | None


class CorrelationController:
    def __init__(self):
        self.alert_repository = SqlSecurityEventRepository()
        self.telemetry_repository = SqlTelemetryRepository()
        self.correlation_repository = SqlCorrelationRepository()

    def get_context(self, alert_id: int) -> CorrelationContextResponse | None:
        alert = self.alert_repository.get_row_by_id(alert_id)
        if alert is None:
            return None

        start = alert.timestamp - timedelta(seconds=WINDOW_SECONDS)
        end = alert.timestamp + timedelta(seconds=LOOKAHEAD_SECONDS)

        telemetry = self.telemetry_repository.get_between(start, end)

        # Korelacioni opis iz zasebne tabele (ako postoji za ovaj alarm).
        corr = self.correlation_repository.get_by_event_id(alert_id)
        correlation_detail = None
        if corr is not None:
            correlation_detail = CorrelationDetail(
                pattern=corr.pattern,
                base_severity=corr.base_severity,
                final_severity=corr.final_severity,
                network_summary=corr.network_summary,
                process_summary=corr.process_summary,
                link_summary=corr.link_summary,
            )

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
            correlation=correlation_detail,
        )