from application.messaging import (
    Observer,
    Message,
    MessageBus
)
from .topic import ObservableTopic


class InMemoryMessageBus(MessageBus):

    def __init__(self):
        self._observable_topics = dict()  # : Dict[str, ObservableTopic]

    def subscribe(self, observer: Observer, topic: str):
        """ Register an observer to a topic, create an observable topic if not already exists. """
        existing_observable = self._observable_topics.get(topic)
        if not existing_observable:
            existing_observable = self._observable_topics[topic] = ObservableTopic()
        existing_observable.subscribe(observer)

    def unsubscribe(self, observable: Observer, topic: str) -> bool:
        """ Un-register an observer from a topic, remove an observable topic if no observers left. """
        existing_observable = self._observable_topics.get(topic)
        if existing_observable:
            existing_observable.unsubscribe(observable)
            if not existing_observable.subscribers:
                del self._observable_topics[topic]
            is_unsubscribed = True
        else:
            is_unsubscribed = False
        return is_unsubscribed

    def unsubscribe_all(self, observer: Observer):
        for observable_topic in self._observable_topics.values():
            if observable_topic.is_subscribed(observer):
                observable_topic.unsubscribe(observer)

    def is_subscribed(self, observer: Observer, topic: str) -> bool:
        observable_topic = self._observable_topics.get(topic)
        if observable_topic:
            is_subscribed = observable_topic.is_subscribed(observer)
        else:
            is_subscribed = False
        return is_subscribed

    def subscribed_on(self, observer: Observer) -> list:
        topics = list()
        for topic_id, observable_topic in self._observable_topics.items():
            if observable_topic.is_subscribed(observer):
                topics.append(topic_id)
        return topics

    def publish(self, topic: str, msg: Message) -> bool:
        observable_topic = self._observable_topics.get(topic)
        if observable_topic and observable_topic.subscribers:
            observable_topic.notify(msg)
            is_notified = True
        else:
            is_notified = False
        return is_notified
