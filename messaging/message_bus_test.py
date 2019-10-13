import unittest
from unittest.mock import Mock
from application.messaging import (
    Observer,
    Message
)
from .message_bus import (
    InMemoryMessageBus,
)


default_topic = "/message/updates"
another_topic = "/message/request"


class TestInMemoryMessageBus(unittest.TestCase):

    def test_subscribe_on_topic(self):
        msg_bus = InMemoryMessageBus()
        observer = Mock(spec=Observer)
        msg_bus.subscribe(observer, default_topic)
        self.assertTrue(msg_bus.is_subscribed(observer, default_topic))

    def test_topic_id(self):
        """ Test that different Topic-objects with same content is treated as same topic """
        msg_bus = InMemoryMessageBus()
        observer = Mock(spec=Observer)
        msg_bus.subscribe(observer, default_topic)
        self.assertTrue(msg_bus.is_subscribed(observer, default_topic))

    def test_unsubscribe_on_topic(self):
        msg_bus = InMemoryMessageBus()
        observer = Mock(spec=Observer)
        msg_bus.subscribe(observer, default_topic)
        msg_bus.unsubscribe(observer, default_topic)
        self.assertFalse(msg_bus.is_subscribed(observer, default_topic))

    def test_unsubscribe_on_invalid_topic(self):
        msg_bus = InMemoryMessageBus()
        observer = Mock(spec=Observer)
        is_unsubscribed = msg_bus.unsubscribe(observer, default_topic)
        self.assertFalse(is_unsubscribed)

    def test_unsubscribe_all(self):
        msg_bus = InMemoryMessageBus()
        observer = Mock(spec=Observer)
        msg_bus.subscribe(observer, default_topic)
        msg_bus.subscribe(observer, another_topic)
        msg_bus.unsubscribe_all(observer)
        self.assertFalse(msg_bus.is_subscribed(observer, default_topic))
        self.assertFalse(msg_bus.is_subscribed(observer, another_topic))

    def test_get_subscribed_topics(self):
        msg_bus = InMemoryMessageBus()
        observer = Mock(spec=Observer)
        msg_bus.subscribe(observer, default_topic)
        msg_bus.subscribe(observer, another_topic)
        self.assertEqual([default_topic, another_topic], msg_bus.subscribed_on(observer))

    def test_notify(self):
        msg_bus = InMemoryMessageBus()
        first_observer = Mock(spec=Observer)
        second_observer = Mock(spec=Observer)
        msg_bus.subscribe(first_observer, default_topic)
        msg_bus.subscribe(second_observer, default_topic)
        msg = Mock(spec=Message)
        msg_bus.publish(default_topic, msg)
        first_observer.notify.assert_called_once_with(msg)
        second_observer.notify.assert_called_once_with(msg)

    def test_publish_when_no_subscribers(self):
        msg_bus = InMemoryMessageBus()
        observer = Mock(spec=Observer)
        msg_bus.subscribe(observer, default_topic)
        msg_bus.unsubscribe_all(observer) # topic will still exist here, but with no subscribers
        msg = Mock(spec=Message)
        res = msg_bus.publish(default_topic, msg)
        self.assertFalse(res)


if __name__ == '__main__':
    unittest.main()