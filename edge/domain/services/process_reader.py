from abc import ABC, abstractmethod


class ProcessReader(ABC):
    @abstractmethod
    async def run(self) -> None:
        ...