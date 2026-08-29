from abc import ABC, abstractmethod

from edge.domain.models.flow import Flow


class InventoryService(ABC):
    @abstractmethod
    def observe_flow(self, flow: Flow) -> None:
        ...