from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from edge.domain.enums.event_type import EventType
from edge.domain.enums.protocol import Protocol
from edge.domain.enums.severity import Severity


@dataclass
class Event:
    timestamp: datetime
    event_type: EventType
    severity: Severity
    source: str
    destination: str
    device: str
    protocol: Protocol
    extra: dict[str, Any] = field(default_factory=dict)