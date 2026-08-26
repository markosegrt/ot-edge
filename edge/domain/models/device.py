from dataclasses import dataclass, field
from datetime import datetime

from edge.domain.enums.device_status import DeviceStatus
from edge.domain.enums.device_type import DeviceType


@dataclass
class Device:
    ip: str
    mac: str | None
    device_type: DeviceType
    status: DeviceStatus
    vendor: str | None
    first_seen: datetime
    last_seen: datetime
    peers: list[str] = field(default_factory=list)