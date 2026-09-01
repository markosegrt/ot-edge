from dataclasses import dataclass, field
from typing import Any

from edge.domain.enums.severity import Severity


@dataclass
class CorrelationResult:
    score: int
    final_severity: Severity
    correlated: bool
    details: dict[str, Any] = field(default_factory=dict)