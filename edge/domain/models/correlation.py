from dataclasses import dataclass
from datetime import datetime


@dataclass
class Correlation:
    event_id: int
    pattern: str
    base_severity: str
    final_severity: str
    network_summary: str | None
    process_summary: str | None
    link_summary: str | None
    created_at: datetime
    id: int | None = None