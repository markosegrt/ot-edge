from dataclasses import dataclass

from edge.domain.models.device import Device


@dataclass
class RuleContext:
    devices_by_ip: dict[str, Device]