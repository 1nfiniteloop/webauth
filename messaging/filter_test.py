import unittest

from application.messaging import (
    Observer,
    Message,
)
from .filter import filter_by_type


class FirstMessage(Message):
    pass


class SecondMessage(Message):
    pass


class ObserverStub(Observer):

    def __init__(self):
        self._called = False

    @property
    def is_called(self):
        return self._called

    @filter_by_type
    def on_notify(self, message: FirstMessage):
        self._called = True


class TestMessageFilter(unittest.TestCase):

    def test_notified_on_desired_message_type(self):
        observer = ObserverStub()
        observer.notify(FirstMessage())
        self.assertTrue(observer.is_called)

    def test_not_notified(self):
        observer = ObserverStub()
        observer.notify(SecondMessage())
        self.assertFalse(observer.is_called)


if __name__ == '__main__':
    unittest.main()