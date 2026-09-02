from dataclasses import dataclass
from datetime import datetime

from edge.domain.enums.severity import Severity
from edge.domain.enums.incident_status import IncidentStatus


@dataclass
class Incident:
    device: str
    severity: Severity
    status: IncidentStatus
    opened_at: datetime
    closed_at: datetime | None
    alarm_count: int