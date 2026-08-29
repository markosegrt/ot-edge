from abc import ABC, abstractmethod

from edge.domain.models.device import Device


class DeviceRepository(ABC):
    @abstractmethod
    def get_by_ip(self, ip: str) -> Device | None:
        ...

    @abstractmethod
    def save(self, device: Device) -> None:
        ...

    @abstractmethod
    def get_all(self) -> list[Device]:
        ...