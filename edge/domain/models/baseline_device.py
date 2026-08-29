from dataclasses import dataclass

from edge.domain.enums.device_type import DeviceType


@dataclass
class BaselineDevice:
    ip: str
    device_type: DeviceType
    name: str
    trusted: bool
    can_write: bool = False