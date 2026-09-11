from dataclasses import dataclass
from datetime import datetime

from edge.domain.enums.quality import Quality


@dataclass
class Telemetry:
    timestamp: datetime
    device: str
    device_ip: str
    tag: str
    value: float
    unit: str
    quality: Quality