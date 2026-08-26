from abc import ABC, abstractmethod

from edge.domain.models.telemetry import Telemetry


class TelemetryRepository(ABC):
    @abstractmethod
    def save(self, telemetry: Telemetry) -> None:
        ...

    @abstractmethod
    def get_all(self) -> list[Telemetry]:
        ...