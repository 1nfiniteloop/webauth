import logging

from tornado.websocket import WebSocketHandler
import tornado.web
import tornado.escape

from application import User
from application.messaging import (
    Observer,
    Message,
    MessageBus
)
from unix_account_authorization import (
    topic_user_responses,
    topic_user_requests,
    topic_user_updates,
    MessageProtocol,
    DecodeFailed
)
from .base import AUTH_TOKEN_NAME
from user_serializer import (
    UserSerializer,
)

log = logging.getLogger(__name__)


class UnixAccountAuthorizationWebsocketArguments:

    def __init__(self, msg_bus: MessageBus, user_serializer: UserSerializer, msg_protocol: MessageProtocol):
        self._msg_bus = msg_bus
        self._user_serializer = user_serializer
        self._msg_protocol = msg_protocol

    @property
    def message_bus(self) -> MessageBus:
        return self._msg_bus

    @property
    def user_serializer(self) -> UserSerializer:
        return self._user_serializer

    @property
    def message_protocol(self) -> MessageProtocol:
        return self._msg_protocol


class UnixAccountAuthorizationWebsocket(WebSocketHandler):

    sessions = dict()

    class Session(Observer):

        """ A UserWebsocket client session for a user which can observe a topic and get notified """

        def __init__(self, websocket: WebSocketHandler, msg_protocol: MessageProtocol):
            self._websocket = websocket
            self._msg_protocol = msg_protocol

        def on_notify(self, msg: Message):
            data = self._msg_protocol.encode(msg)
            try:
                self._try_forward_msg_to_websocket(data)
            except tornado.websocket.WebSocketClosedError:
                log.error("Failed to forward message from message bus: websocket is closed")

        def _try_forward_msg_to_websocket(self, data: str):
            if data:
                self._websocket.write_message(data)
                log.debug("Sending message on bus: {msg_data}".format(msg_data=data))
            else:
                log.error("Failed to encode received message from message bus")

    def initialize(self, args: UnixAccountAuthorizationWebsocketArguments):
        self._args = args

    # NOTE: reused from base.py
    def get_current_user(self) -> User:
        client_cookie = self.get_secure_cookie(AUTH_TOKEN_NAME)
        return self.get_authenticated_user(client_cookie)

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._args.user_serializer.unserialize(client_cookie)

    def get(self, *args, **kwargs):
        """ Extend entrypoint and allow only authenticated users on websocket """
        if not self.current_user.id:
            raise tornado.web.HTTPError(401)
        super().get(*args, **kwargs)

    def get_compression_options(self):
        # a Non-None value enables compression with default options. ref: ?
        return {}

    def open(self):
        self._new_user_session()

    def _new_user_session(self):
        current_user = self.current_user
        user_id = current_user.id
        user_session = self.Session(self, self._args.message_protocol)
        self._args.message_bus.subscribe(user_session, topic_user_requests(user_id))
        self._args.message_bus.subscribe(user_session, topic_user_updates(user_id))
        self.sessions[user_id] = user_session
        log.info("Client connected '{name}' id: {id}".format(name=current_user.name, id=current_user.id))

    def on_close(self):
        self._cleanup_user_session()

    def _cleanup_user_session(self):
        current_user = self.current_user
        user_id = current_user.id
        user_session = self.sessions[user_id]
        self._args.message_bus.unsubscribe_all(user_session)
        del user_session
        log.info("Client disconnected '{name}' id: {id}".format(name=current_user.name, id=current_user.id))

    def on_message(self, data):
        try:
            message = self._args.message_protocol.decode(data)
            self._forward_message(message)
            log.debug("Forward received message on bus: {msg_data}".format(msg_data=data))
        except DecodeFailed as err:
            self._reply_error(str(err))

    def _forward_message(self, message: Message):
        success = self._args.message_bus.publish(topic_user_responses(self.current_user.id), message)
        if not success:
            self._reply_error("Internal error, failed to forward message on bus (topic don't exist)")

    def _reply_error(self, error_text: str):
        """ Reply client with a control message """
        log.error(error_text)
        error_msg = self._args.message_protocol.encode_error(error_text)
        self.write_message(error_msg)
