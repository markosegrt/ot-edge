from abc import ABC, abstractmethod

from edge.domain.models.event import Event
from edge.domain.models.flow import Flow


class Normalizer(ABC):
    @abstractmethod
    def from_flow(self, flow: Flow) -> Event:
        ...