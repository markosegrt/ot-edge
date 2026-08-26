# edge/domain/repositories/flow_repository.py
from abc import ABC, abstractmethod

from edge.domain.models.flow import Flow


class FlowRepository(ABC):
    @abstractmethod
    def save(self, flow: Flow) -> None:
        ...

    @abstractmethod
    def get_all(self) -> list[Flow]:
        ...