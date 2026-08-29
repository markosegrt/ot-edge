from abc import ABC, abstractmethod

from edge.domain.models.event import Event
from edge.domain.models.flow import Flow
from datetime import datetime

class Normalizer(ABC):
    @abstractmethod
    def from_flow(self, flow: Flow) -> Event:
        ...

    @abstractmethod
    def from_modbus_write(
        self, src_ip: str, dst_ip: str, src_port: int, dst_port: int,
        function_code: int, start_address: int | None, timestamp: datetime,
    ) -> Event:
        ...