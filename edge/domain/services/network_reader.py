from abc import ABC, abstractmethod

class NetworkReader(ABC):
    @abstractmethod
    def run(self) -> None:
        ...