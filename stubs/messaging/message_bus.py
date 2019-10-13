from application.messaging import (
    Message,
    MessageBus,
    Observer
)

from ..response_mixin import StubResponseMixin

class MessageBusStub(MessageBus, StubResponseMixin):

    def __init__(self):
        self.subscribers = dict()
        super(MessageBusStub).__init__()

    def default_response_data(self) -> dict:
        response_data = {
            "unsubscribe": True,
            "is_subscribed": True,
            "subscribed_on": [],
            "publish": True
        }
        return response_data

    def subscribe(self, observer: Observer, topic: str):
        """ Register an observer to a topic """
        self.subscribers[topic] = observer

    def unsubscribe(self, observer: Observer, topic: str) -> bool:
        """ Un-register an observer from a topic, Returns True on success """
        return self.get_response()

    def unsubscribe_all(self, observer: Observer):
        pass

    def is_subscribed(self, observer: Observer, topic: str) -> bool:
        return self.get_response()

    def subscribed_on(self, observer: Observer) -> list:
        return self.get_response()

    def publish(self, topic: str, msg: Message) -> bool:
        """ Just publish to the attached subscriber """
        return self.get_response()
