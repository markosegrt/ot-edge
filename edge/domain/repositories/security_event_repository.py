from abc import ABC, abstractmethod

from edge.domain.models.security_alert import SecurityAlert


class SecurityEventRepository(ABC):
    @abstractmethod
    def save(self, alert: SecurityAlert) -> None:
        ...

    @abstractmethod
    def get_all(self) -> list[SecurityAlert]:
        ...