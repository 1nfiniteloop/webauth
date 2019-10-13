from abc import (
    ABC,
    abstractmethod
)


class Message(ABC):
    """ Interface for implementing messages """
    pass


class Observer(ABC):

    def notify(self, msg: Message):
        self.on_notify(msg)

    @abstractmethod
    def on_notify(self, message: Message):
        pass


class Observable(ABC):

    @abstractmethod
    def subscribe(self, observer: Observer):
        pass

    @abstractmethod
    def unsubscribe(self, observer: Observer) -> bool:
        pass

    @abstractmethod
    def is_subscribed(self, observer: Observer) -> bool:
        pass

    @property
    @abstractmethod
    def subscribers(self) -> list:
        pass

    @abstractmethod
    def notify(self, msg: Message):
        pass

