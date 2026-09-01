from abc import ABC, abstractmethod
from datetime import datetime

from edge.domain.models.telemetry import Telemetry


class TelemetryRepository(ABC):
    @abstractmethod
    def save(self, telemetry: Telemetry) -> None:
        ...

    @abstractmethod
    def get_all(self) -> list[Telemetry]:
        ...

    @abstractmethod
    def get_between(self, start: datetime, end: datetime) -> list[Telemetry]:
        ...