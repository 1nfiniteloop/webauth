from unittest.mock import (
    ANY,
    call,
    Mock
)

from tornado.testing import AsyncHTTPTestCase
import tornado.web
import tornado.websocket
import tornado.httpclient

from application import User
from application.messaging import (
    MessageBus,
    Message
)
from stubs import (
    UserSerializerStub,
    UnprivilegedUser
)
from unix_account_authorization import (
    MessageProtocol,
    topic_user_requests,
    topic_user_updates,
    topic_user_responses,
    DecodeFailed
)

from .unix_account_authorization_ws import (
    UnixAccountAuthorizationWebsocket,
    UnixAccountAuthorizationWebsocketArguments
)


default_user = User(id_="1234-5678", name="not-admin", privilege=User.Privilege.USER)



class MessageStub(Message):
    pass


class TestUnixAccountAuthorizationWebsocket(AsyncHTTPTestCase):
    API_ENDPOINT = "/api/unix_account/ws"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_serializer = UserSerializerStub()
        self._message_protocol = Mock(spec=MessageProtocol)
        self._message_bus = Mock(spec=MessageBus)

    def setUp(self):
        super().setUp()
        self._reset_stubs()

    def _reset_stubs(self):
        self._message_protocol.reset_mock()
        self._message_bus.reset_mock()
        self._user_serializer.set_response_data_for("unserialize", default_user)

    def _set_logged_in_user(self, user: User):
        self._user_serializer.set_response_data_for("unserialize", user)

    def get_app(self):
        args = UnixAccountAuthorizationWebsocketArguments(
            self._message_bus,
            self._user_serializer,
            self._message_protocol
        )
        app = tornado.web.Application(
            websocket_ping_interval=1,
            cookie_secret="secret",
            handlers=[
                (self.API_ENDPOINT, UnixAccountAuthorizationWebsocket, dict(args=args)),
            ])
        return app

    def get_ws_url(self) -> str:
        url = "ws://localhost:{port}{path}".format(
            port=self.get_http_port(),
            path=self.API_ENDPOINT
        )
        return url

    @tornado.testing.gen_test
    async def test_connect_with_non_logged_in_user(self):
        self._user_serializer.set_response_data_for("unserialize", UnprivilegedUser())
        with self.assertRaisesRegex(tornado.httpclient.HTTPClientError, "Unauthorized$"):
            _ = await tornado.websocket.websocket_connect(self.get_ws_url())

    @tornado.testing.gen_test
    async def test_fail_decode_received_message(self):
        """ Expects to get a control message back saying error """
        expected_error_response = "Oops, error!"
        self._message_protocol.encode_error.return_value = expected_error_response
        self._message_protocol.decode.side_effect = DecodeFailed(expected_error_response)
        ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        ws.write_message("a bad formatted message")
        resp = await ws.read_message()
        self.assertEqual(expected_error_response, resp)
        self._message_protocol.encode_error.assert_called_with(expected_error_response)
        ws.close()

    @tornado.testing.gen_test
    async def test_fail_publish_received_message(self):
        """ Expects to get a control message back saying error """
        expected_error_response = "Oops, error!"
        self._message_protocol.encode_error.return_value = expected_error_response
        self._message_bus.publish.return_value = False
        ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        ws.write_message("Hello, server!")
        resp = await ws.read_message()
        self.assertEqual(expected_error_response, resp)
        ws.close()

    # @tornado.testing.gen_test
    # async def test_encode_msg_failed_when_sending(self):
    #     self._message_protocol.set_response_data_for("encode", "")  # empty message signalling that it failed to encode
    #     ws = await tornado.websocket.websocket_connect(self.get_ws_url())
    #     ws.write_message("bad formatted message")
    #     msg = await ws.read_message()
    #     # how to assert this? we can only know from log messages?
    #     ws.close()

    @tornado.testing.gen_test
    async def test_subscribe_on_requests_and_updates_when_connecting(self):
        expected_calls = [
            call(ANY, topic_user_requests(default_user.id)),
            call(ANY, topic_user_updates(default_user.id))
        ]
        ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        self._message_bus.subscribe.assert_has_calls(expected_calls)
        ws.close()

    @tornado.testing.gen_test
    async def test_unsubscribe_on_disconnection(self):
        ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        ws.close()
        _ = await ws.read_message()  # websocket sends a None message on disconnect
        self._message_bus.unsubscribe_all.assert_called_once()

    @tornado.testing.gen_test
    async def test_forward_message_received(self):
        expected_calls = [
            call(topic_user_responses(default_user.id), ANY)
        ]
        ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        ws.write_message("Hello, server!")
        ws.close()
        _ = await ws.read_message()  # websocket sends a None message on disconnect
        self._message_bus.publish.assert_has_calls(expected_calls)

    @tornado.testing.gen_test
    async def test_forward_decoded_message_received(self):
        """ Tests that it's actually the decoded message which gets published on message bus """
        expected_decoded_data = "decoded message!"
        self._message_protocol.decode.return_value = expected_decoded_data
        expected_calls = [
            call(topic_user_responses(default_user.id), expected_decoded_data)
        ]
        ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        ws.write_message("Hello, server!")
        ws.close()
        _ = await ws.read_message()  # websocket sends a None message on disconnect
        self._message_bus.publish.assert_has_calls(expected_calls)

    @tornado.testing.gen_test
    async def test_multiple_sessions(self):
        expected_calls_subscribe = [
            call(ANY, topic_user_requests(default_user.id)),
            call(ANY, topic_user_requests(default_user.id)),
            call(ANY, topic_user_requests(default_user.id)),
            call(ANY, topic_user_updates(default_user.id)),
            call(ANY, topic_user_updates(default_user.id)),
            call(ANY, topic_user_updates(default_user.id)),
        ]
        expected_calls_unsubscribe = [
            call(ANY),
            call(ANY),
            call(ANY),
        ]
        first_ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        second_ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        third_ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        first_ws.close()
        second_ws.close()
        third_ws.close()
        # websocket sends a None message on disconnect
        _ = await first_ws.read_message()
        _ = await second_ws.read_message()
        _ = await third_ws.read_message()
        self._message_bus.subscribe.assert_has_calls(expected_calls_subscribe, any_order=True)
        self._message_bus.unsubscribe_all.assert_has_calls(expected_calls_unsubscribe)

    @tornado.testing.gen_test
    async def test_notify_wesocket(self):
        expected_response = "Hello, client!"
        self._message_protocol.encode.return_value = expected_response
        ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        observer = self._message_bus.subscribe.call_args_list[0][0][0]  # get the observer provided on first call to "msg_bus.subscribe(websocket_session)"
        observer.notify(MessageStub())
        resp = await ws.read_message()
        ws.close()
        self.assertEqual(expected_response, resp)

    @tornado.testing.gen_test
    async def test_notify_closed_wesocket(self):
        ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        ws.close()
        _ = await ws.read_message() # websocket sends a None message on disconnect
        observer = self._message_bus.subscribe.call_args_list[0][0][0]  # get the observer provided on first call to "msg_bus.subscribe(websocket_session)"
        observer.notify(MessageStub())
        # how to assert? as long as it don't throw it passes...
