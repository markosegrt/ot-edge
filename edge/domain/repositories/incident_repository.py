from abc import ABC, abstractmethod
from datetime import datetime

from edge.domain.models.incident import Incident


class IncidentRepository(ABC):
    @abstractmethod
    def save(self, incident: Incident) -> int:
        ...

    @abstractmethod
    def get_open_for_device(self, device: str, since: datetime) -> Incident | None:
        ...

    @abstractmethod
    def increment_alarm_count(self, incident_id: int) -> None:
        ...