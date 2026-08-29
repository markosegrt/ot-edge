from abc import ABC, abstractmethod

from edge.domain.models.flow import Flow


class EventProcessor(ABC):
    @abstractmethod
    def process_flow(self, flow: Flow) -> None:
        ...

    @abstractmethod
    def process_modbus_write(self, write_data: dict) -> None:
        ...