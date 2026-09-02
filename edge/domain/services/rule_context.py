from dataclasses import dataclass, field

from edge.domain.models.device import Device
from edge.domain.models.baseline_device import BaselineDevice


@dataclass
class RuleContext:
    devices_by_ip: dict[str, Device]
    baseline_by_ip: dict[str, BaselineDevice] = field(default_factory=dict)
    ports_by_source: dict[str, set[int]] = field(default_factory=dict)