from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from edge.domain.enums.event_type import EventType
from edge.domain.enums.protocol import Protocol
from edge.domain.enums.severity import Severity


@dataclass
class SecurityAlert:
    timestamp: datetime
    rule_id: str
    severity: Severity
    event_type: EventType
    source: str
    destination: str
    device: str
    protocol: Protocol
    correlated: bool = False
    extra: dict[str, Any] = field(default_factory=dict)