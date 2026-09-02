from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AlertRow:
    """Read model za API — sadrzi id koji domain SecurityAlert nema,
    jer front referencira konkretan alarm za korelacioni kontekst."""
    id: int
    timestamp: datetime
    rule_id: str | None
    severity: str
    source: str
    destination: str
    protocol: str
    correlated: bool
    occurrence_count: int
    extra: dict[str, Any] = field(default_factory=dict)