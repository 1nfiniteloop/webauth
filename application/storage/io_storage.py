from abc import (
    ABC,
    abstractmethod
)


class IOStorage(ABC):

    @abstractmethod
    def read(self) -> str:
        pass

    @abstractmethod
    def write(self, data: str):
        pass
