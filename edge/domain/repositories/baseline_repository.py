from abc import ABC, abstractmethod

from edge.domain.models.baseline_device import BaselineDevice


class BaselineRepository(ABC):
    @abstractmethod
    def get_all(self) -> list[BaselineDevice]:
        ...

    @abstractmethod
    def get_by_ip(self, ip: str) -> BaselineDevice | None:
        ...

    @abstractmethod
    def create(self, device: BaselineDevice) -> None:
        ...

    @abstractmethod
    def update(self, ip: str, device: BaselineDevice) -> None:
        ...

    @abstractmethod
    def delete(self, ip: str) -> None:
        ...