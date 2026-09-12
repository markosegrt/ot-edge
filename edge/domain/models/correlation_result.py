from dataclasses import dataclass, field
from typing import Any

from edge.domain.enums.severity import Severity


@dataclass
class CorrelationResult:
    score: int
    final_severity: Severity
    correlated: bool
    details: dict[str, Any] = field(default_factory=dict)
    pattern: str | None = None            
    base_severity: Severity | None = None  
    network_summary: str | None = None     
    process_summary: str | None = None     
    link_summary: str | None = None        