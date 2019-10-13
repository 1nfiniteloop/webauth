from abc import (
    ABC,
    abstractmethod
)

from .observable import (
    Message,
    Observer
)


class MessageBus(ABC):

    """ Similar impl for MQTT:
    https://www.eclipse.org/paho/files/javadoc/org/eclipse/paho/client/mqttv3/MqttClient.html
    """

    @abstractmethod
    def subscribe(self, observer: Observer, topic: str):
        """ Register an observer to a topic """
        pass

    @abstractmethod
    def unsubscribe(self, observer: Observer, topic: str) -> bool:
        """ Un-register an observer from a topic, Returns True on success """
        pass

    @abstractmethod
    def unsubscribe_all(self, observer: Observer):
        pass

    @abstractmethod
    def is_subscribed(self, observer: Observer, topic: str) -> bool:
        pass

    @abstractmethod
    def subscribed_on(self, observer: Observer) -> list:
        pass

    @abstractmethod
    def publish(self, topic: str, msg: Message) -> bool:
        """ Returns True if topic exist and has subscribers """
        pass