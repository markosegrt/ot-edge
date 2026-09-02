from abc import ABC, abstractmethod
from datetime import datetime

from edge.domain.models.security_alert import SecurityAlert


class SecurityEventRepository(ABC):
    @abstractmethod
    def save(self, alert: SecurityAlert) -> None:
        ...

    @abstractmethod
    def get_all(self) -> list[SecurityAlert]:
        ...

    @abstractmethod
    def find_recent_duplicate_id(
        self, rule_id: str, source: str, destination: str, since: datetime
    ) -> int | None:
        ...

    @abstractmethod
    def increment_occurrence(self, alert_id: int) -> None:
        ...