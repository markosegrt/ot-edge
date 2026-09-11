from dataclasses import dataclass, field
from typing import Any

from edge.domain.enums.severity import Severity


@dataclass
class RuleConfig:
    rule_id: str
    name: str
    enabled: bool
    severity: Severity
    params: dict[str, Any] = field(default_factory=dict)