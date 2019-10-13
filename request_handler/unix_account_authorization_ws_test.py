import asyncio
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
    StubResponseMixin,
    UnprivilegedUser
)
from unix_account_authorization import (
    topic_user_requests,
    topic_user_updates,
    topic_user_responses,
    DecodeFailed
)

from .unix_account_authorization_ws import (
    UnixAccountAuthorizationWebsocket,
    UnixAccountAuthorizationWebsocketArguments
)

from unix_account_authorization import MessageProtocol


default_user = User(id_="1234-5678", name="not-admin", privilege=User.Privilege.USER)



class MessageStub(Message):
    pass


class MessageProtocolStub(MessageProtocol, StubResponseMixin):

    def default_response_data(self) -> dict:
        response_data = {
            "decode": MessageStub(),
            "encode": "",
            "encode_error": "error"
        }
        return response_data

    def decode(self, data: str) -> Message:
        return self.get_response()

    def encode(self, msg: Message) -> str:
        return self.get_response()

    def encode_error(self, error_text: str) -> str:
        return self.get_response()


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
        # self._ws = tornado.websocket.websocket_connect(url)  # NOTE: returns an awaitable/future something..

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
            ws = await tornado.websocket.websocket_connect(self.get_ws_url())

    @tornado.testing.gen_test
    async def test_fail_decoding_received_message(self):
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
        ws.write_message("bla bla")
        resp = await ws.read_message()
        self.assertEqual(expected_error_response, resp)
        ws.close()

    # @tornado.testing.gen_test
    # async def test_encode_msg_failed_when_sending(self):
    #     self._message_protocol.set_response_data_for("encode", "")  # empty message signalling that it failed to encode
    #     ws = await tornado.websocket.websocket_connect(self.get_ws_url())
    #     ws.write_message("bad formatted message")
    #     msg = await ws.read_message()
    #     # how to assert this? we can only know if websocket
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
        await asyncio.sleep(0.05) # Needs some time for websocket to disconnect
        self._message_bus.unsubscribe_all.assert_called_once()

    @tornado.testing.gen_test
    async def test_forward_message_received(self):
        expected_calls = [
            call(topic_user_responses(default_user.id), ANY)
        ]
        ws = await tornado.websocket.websocket_connect(self.get_ws_url())
        ws.write_message("bla bla")
        ws.close()
        await asyncio.sleep(0.05) # Needs some time for websocket to process. TODO can we get around these sleeps? Instrument the websocket?
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
        ws.write_message("bla bla")
        ws.close()
        await asyncio.sleep(0.05)
        self._message_bus.publish.assert_has_calls(expected_calls)

    # @tornado.testing.gen_test
    # async def test_notify_wesocket(self):
    #     expected_response = "Hello, client"
    #     self._message_protocol.encode.return_value = expected_response
    #     ws = await tornado.websocket.websocket_connect(self.get_ws_url())
    #     ws.write_message(json.dumps({"message": "Hello, server!"}))
    #     # get observer
    #     topic_id = "/user/" + default_user.id   # construct this from class instead, as in the real code
    #     websocket_session = self._message_bus.subscribers[topic_id]
    #     websocket_session.notify(expected_response)
    #     response = await ws.read_message()
    #     ws.close()
    #     self.assertEqual(expected_response, response)
