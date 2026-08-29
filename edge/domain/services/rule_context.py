# edge/domain/services/rule_context.py
from dataclasses import dataclass, field

from edge.domain.models.device import Device
from edge.domain.models.baseline_device import BaselineDevice


@dataclass
class RuleContext:
    devices_by_ip: dict[str, Device]
    baseline_by_ip: dict[str, BaselineDevice] = field(default_factory=dict)