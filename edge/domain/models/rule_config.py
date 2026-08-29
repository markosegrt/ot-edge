from dataclasses import dataclass

from edge.domain.enums.severity import Severity


@dataclass
class RuleConfig:
    rule_id: str
    name: str
    enabled: bool
    severity: Severity