from abc import ABC, abstractmethod
from datetime import datetime

from edge.domain.models.flow import Flow


class InventoryService(ABC):
    @abstractmethod
    def observe_flow(self, flow: Flow) -> None:
        ...

    @abstractmethod
    def check_availability(self, reference_time: datetime) -> None:
        ...