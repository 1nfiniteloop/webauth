import unittest
from unittest.mock import Mock

from .topic import ObservableTopic
from application.messaging import (
    Observer
)


class TestObservableTopic(unittest.TestCase):

    def test_subscribe(self):
        observer = Mock(spec=Observer)
        topic = ObservableTopic()
        topic.subscribe(observer)
        self.assertTrue(topic.is_subscribed(observer))

    def test_subscribe_unsubscribe(self):
        observer = Mock(spec=Observer)
        topic = ObservableTopic()
        topic.subscribe(observer)
        topic.unsubscribe(observer)
        self.assertFalse(topic.is_subscribed(observer))

    def test_unregister_nonexisting_observer(self):
        observer = Mock(spec=Observer)
        topic = ObservableTopic()
        unsubscribed = topic.unsubscribe(observer)
        self.assertFalse(unsubscribed)

    def test_notify(self):
        msg = Mock()
        first_observer = Mock(spec=Observer)
        second_observer = Mock(spec=Observer)
        topic = ObservableTopic()
        topic.subscribe(first_observer)
        topic.subscribe(second_observer)
        topic.notify(msg)
        first_observer.notify.assert_called_once_with(msg)
        second_observer.notify.assert_called_once_with(msg)
