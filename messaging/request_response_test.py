import asyncio
import unittest
from unittest.mock import (
    Mock,
    call,
    ANY
)
from datetime import datetime, timedelta

from application.messaging import (
    MessageBus,
    Message,
    Observer
)
from .request_response import (
    Request,
    ResponseCallback,
    SendPolicy
)

loop = asyncio.new_event_loop()


def run_parallel(coroutines: list):
    loop.run_until_complete(asyncio.gather(*coroutines, loop=loop))


def async_test(coro):
    def wrapper(*args, **kwargs):
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


def get_expiration_timestamp(seconds: float) -> datetime:
    return datetime.now() + timedelta(seconds=seconds)


class MessageStub(Message):
    pass


class MessageBusStub(MessageBus):

    """ Needed when simulate a request/response in one test case """

    def __init__(self):
        self._topics = dict()

    def subscribe(self, observer: Observer, topic: str):
        """ Register an observer to a topic """
        self._topics[topic] = observer

    def unsubscribe(self, observer: Observer, topic: str) -> bool:
        pass

    def unsubscribe_all(self, observer: Observer):
        pass

    def is_subscribed(self, observer: Observer, topic: str) -> bool:
        pass

    def subscribed_on(self, observer: Observer) -> list:
        pass

    def publish(self, topic: str, msg: Message) -> bool:
        pass

    def trigger_publish(self, topic: str, msg: Message):
        observer = self._topics[topic]
        observer.notify(msg)


default_request_topics = ["first_user/request", "second_user/request"]
default_response_topics = ["first_user/response", "second_user/response"]
default_expiration_time = datetime.now()
default_request_message = MessageStub()
default_response_message = MessageStub()


class TestRequestResponse(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._msg_bus = Mock(spec=MessageBus)

    def setUp(self):
        self._reset_stubs()

    def _reset_stubs(self):
        self._msg_bus.reset_mock()

    @async_test
    async def test_subscribe_on_all_response_topics(self):
        expected_calls = [
            call(ANY, default_response_topics[0]),
            call(ANY, default_response_topics[1]),
        ]
        response = Mock(spec=ResponseCallback)
        request = Request(
            self._msg_bus,
            response,
            default_request_topics,
            default_response_topics,
        )
        success = await request.send(default_request_message, default_expiration_time)
        self._msg_bus.subscribe.assert_has_calls(expected_calls)

    @async_test
    async def test_unsubscribe_on_all_response_topics(self):
        response = Mock(spec=ResponseCallback)
        request = Request(
            self._msg_bus,
            response,
            default_request_topics,
            default_response_topics,
        )
        success = await request.send(default_request_message, default_expiration_time)
        self._msg_bus.unsubscribe_all.assert_called_once()

    @async_test
    async def test_publish_to_all_request_topics(self):
        self._msg_bus.publish.return_value = True
        expected_calls = [
            call(default_request_topics[0], default_request_message),
            call(default_request_topics[1], default_request_message),
        ]
        response = Mock(spec=ResponseCallback)
        request = Request(
            self._msg_bus,
            response,
            default_request_topics,
            default_response_topics,
        )
        success = await request.send(default_request_message, default_expiration_time)
        self._msg_bus.publish.assert_has_calls(expected_calls)

    @async_test
    async def test_send_using_policy_to_all(self):
        self._msg_bus.publish.return_value = True
        response = Mock(spec=ResponseCallback)
        request = Request(
            self._msg_bus,
            response,
            default_request_topics,
            default_response_topics,
            policy=SendPolicy.ALL
        )
        success = await request.send(default_request_message, default_expiration_time)
        self.assertTrue(success)

    @async_test
    async def test_send_failed_using_policy_to_all(self):
        self._msg_bus.publish.side_effect = [True, False]
        response = Mock(spec=ResponseCallback)
        request = Request(
            self._msg_bus,
            response,
            default_request_topics,
            default_response_topics,
            policy=SendPolicy.ALL
        )
        success = await request.send(default_request_message, default_expiration_time)
        self.assertFalse(success)

    @async_test
    async def test_send_using_policy_at_least_one(self):
        self._msg_bus.publish.return_value = [True, False]
        response = Mock(spec=ResponseCallback)
        request = Request(
            self._msg_bus,
            response,
            default_request_topics,
            default_response_topics,
            policy=SendPolicy.AT_LEAST_ONE
        )
        success = await request.send(default_request_message, default_expiration_time)
        self.assertTrue(success)

    @async_test
    async def test_send_failed_using_policy_at_least_one(self):
        self._msg_bus.publish.return_value = False
        response = Mock(spec=ResponseCallback)
        request = Request(
            self._msg_bus,
            response,
            default_request_topics,
            default_response_topics,
            policy=SendPolicy.AT_LEAST_ONE
        )
        success = await request.send(default_request_message, default_expiration_time)
        self.assertFalse(success)

    @async_test
    async def test_response_expired(self):
        self._msg_bus.publish.return_value = True
        response = Mock(spec=ResponseCallback)
        request = Request(
            self._msg_bus,
            response,
            default_request_topics,
            default_response_topics,
        )
        success = await request.send(default_request_message, default_expiration_time)
        response.on_expired.assert_called_once()

    def test_one_response_received(self):
        msg_bus = MessageBusStub()
        response = Mock(spec=ResponseCallback)
        request = Request(
            msg_bus,
            response,
            default_request_topics,
            default_response_topics,
        )

        async def async_wrapper():
            await asyncio.sleep(0.2)  # prevents notifying condition before started waiting
            msg_bus.trigger_publish(default_response_topics[0], default_response_message)

        run_parallel([
            request.send(default_request_message, get_expiration_timestamp(1)),
            async_wrapper(),
        ])
        response.on_response.assert_called_once_with(default_response_message)

    def test_many_responses_received(self):
        """ Shall only trigger callback once """
        msg_bus = MessageBusStub()
        response = Mock(spec=ResponseCallback)
        request = Request(
            msg_bus,
            response,
            default_request_topics,
            default_response_topics,
        )

        async def async_wrapper():
            await asyncio.sleep(0.2)  # prevents notifying condition before started waiting
            for topic in default_response_topics:
                msg_bus.trigger_publish(topic, default_response_message)

        run_parallel([
            request.send(default_request_message, get_expiration_timestamp(1)),
            async_wrapper(),
        ])
        response.on_response.assert_called_once_with(default_response_message)