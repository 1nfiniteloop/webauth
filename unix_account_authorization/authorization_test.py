import asyncio
from typing import (
    Any,
    Callable,
    List
)
import unittest
from unittest.mock import (
    ANY,
    call,
    Mock
)

from application.messaging import MessageBus
from messaging import (
    Request,
    ResponseCallback
)
from storage import NonExistingHost
from .authorization import (
    AuthorizationRequestSubject,
    UnixAccountAuthorizationRequest,
    AuthorizationRequestBuilder,
)
from .state import AuthorizationState
from .messages import AuthorizationResponseMessage
from .topics import topic_user_updates

from stubs import (
    UnixAccountStorageStub,
    HostStorageStub,
    MessageBusStub,
)

loop = asyncio.new_event_loop()

valid_subject = AuthorizationRequestSubject(host_id="1234", unix_account_id=1000, service_name="login", timeout=30)



def async_test(coro):
    def wrapper(*args, **kwargs):
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


class RequestStub:

    """ Mimics the signature of Request class """

    def __init__(self, set_send_return_value: bool = True):
        self._send_return_value = set_send_return_value

    async def send(self, *args):
        return self._send_return_value


class AuthorizationRequestBuilderStub(AuthorizationRequestBuilder):

    """ Used in test cases where ResponseCallback is need """

    def __init__(self, response_callback_actor: Callable[[ResponseCallback], Any]):
        self._response_callback_actor = response_callback_actor

    def new(self, msg_bus: MessageBus, users_id: List[str], response_cb: ResponseCallback) -> Request:
        self._response_callback_actor(response_cb)
        return RequestStub()


class TestUnixAccountAuthorizationRequest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._host_storage = HostStorageStub()
        self._unix_account_storage = UnixAccountStorageStub()

    def setUp(self):
        self._reset_stubs()

    def _reset_stubs(self):
        self._host_storage.reset_stub()
        self._unix_account_storage.reset_stub()

    @async_test
    async def test_host_does_not_exists(self):
        request_builder = Mock(spec=AuthorizationRequestBuilder)
        request_builder.new.return_value = RequestStub()
        self._host_storage.set_response_data_for("get_host_by_id", NonExistingHost())
        req = UnixAccountAuthorizationRequest(
            MessageBusStub(),
            self._unix_account_storage,
            self._host_storage,
            request_builder
        )
        resp = await req.authorize(valid_subject)
        self.assertEqual(resp.state, AuthorizationState.ERROR)
        self.assertRegex(resp.message, "Host .* not found")

    @async_test
    async def test_no_users_id_associated(self):
        request_builder = Mock(spec=AuthorizationRequestBuilder)
        request_builder.new.return_value = RequestStub()
        self._unix_account_storage.set_response_data_for("get_associated_users_for_unix_account", [])
        req = UnixAccountAuthorizationRequest(
            MessageBusStub(),
            self._unix_account_storage,
            self._host_storage,
            request_builder
        )
        resp = await req.authorize(valid_subject)
        self.assertEqual(resp.state, AuthorizationState.ERROR)
        self.assertRegex(resp.message, "No users found")

    @async_test
    async def test_error_response_when_send_failed(self):
        request_builder = Mock(spec=AuthorizationRequestBuilder)
        request_builder.new.return_value = RequestStub(set_send_return_value=False)
        req = UnixAccountAuthorizationRequest(
            MessageBusStub(),
            self._unix_account_storage,
            self._host_storage,
            request_builder
        )
        resp = await req.authorize(valid_subject)
        self.assertEqual(resp.state, AuthorizationState.ERROR)
        self.assertRegex(resp.message, "Failed to send request")

    @async_test
    async def test_publish_updates_on_timeout(self):
        user_id = "1234"
        self._unix_account_storage.set_response_data_for("get_associated_users_for_unix_account", [user_id])
        msg_bus = Mock(spec=MessageBus)
        request_builder = AuthorizationRequestBuilderStub(response_callback_actor=lambda response_cb: response_cb.on_expired())
        req = UnixAccountAuthorizationRequest(
            msg_bus,
            self._unix_account_storage,
            self._host_storage,
            request_builder
        )
        resp = await req.authorize(valid_subject)
        expected_calls = [
            call(topic_user_updates(user_id), ANY),
        ]
        msg_bus.publish.assert_has_calls(expected_calls)

    @async_test
    async def test_publish_updates_on_responses(self):
        user_id = "1234"
        self._unix_account_storage.set_response_data_for("get_associated_users_for_unix_account", [user_id])
        msg_bus = Mock(spec=MessageBus)
        msg = AuthorizationResponseMessage("request-id", AuthorizationState.AUTHORIZED)
        request_builder = AuthorizationRequestBuilderStub(
            response_callback_actor=lambda response_cb: response_cb.on_response(msg)
        )
        req = UnixAccountAuthorizationRequest(
            msg_bus,
            self._unix_account_storage,
            self._host_storage,
            request_builder
        )
        resp = await req.authorize(valid_subject)
        expected_calls = [
            call(topic_user_updates(user_id), ANY),
        ]
        msg_bus.publish.assert_has_calls(expected_calls)

    @async_test
    async def test_response_authorized(self):
        request_builder = AuthorizationRequestBuilderStub(
            response_callback_actor=lambda response_cb: response_cb.on_response(AuthorizationResponseMessage("msg-id", AuthorizationState.AUTHORIZED))
        )
        req = UnixAccountAuthorizationRequest(
            Mock(spec=MessageBus),
            self._unix_account_storage,
            self._host_storage,
            request_builder
        )
        resp = await req.authorize(valid_subject)
        self.assertEqual(resp.state, AuthorizationState.AUTHORIZED)

    @async_test
    async def test_response_unauthorized(self):
        request_builder = AuthorizationRequestBuilderStub(
            response_callback_actor=lambda response_cb: response_cb.on_response(AuthorizationResponseMessage("msg-id", AuthorizationState.UNAUTHORIZED))
        )
        req = UnixAccountAuthorizationRequest(
            Mock(spec=MessageBus),
            self._unix_account_storage,
            self._host_storage,
            request_builder
        )
        resp = await req.authorize(valid_subject)
        self.assertEqual(resp.state, AuthorizationState.UNAUTHORIZED)

    @async_test
    async def test_response_expired(self):
        request_builder = AuthorizationRequestBuilderStub(
            response_callback_actor=lambda response_cb: response_cb.on_expired()
        )
        req = UnixAccountAuthorizationRequest(
            Mock(spec=MessageBus),
            self._unix_account_storage,
            self._host_storage,
            request_builder
        )
        resp = await req.authorize(valid_subject)
        self.assertEqual(resp.state, AuthorizationState.EXPIRED)
