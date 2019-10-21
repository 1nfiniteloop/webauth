import logging
from typing import (
    Callable,
    Any
)
import uuid

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


class WebsocketSession(Observer):

    """ Websocket session for notify users from message bus on websocket """

    def __init__(self, send_cb: Callable[[Message], Any]):
        self._websocket_send_cb = send_cb

    def on_notify(self, msg: Message):
        self._websocket_send_cb(msg)


class UnixAccountAuthorizationWebsocket(WebSocketHandler):

    sessions = dict()

    def initialize(self, args: UnixAccountAuthorizationWebsocketArguments):
        self._args = args
        self._session_id = uuid.uuid4().hex

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
        current_user = self.current_user
        self._new_session(current_user.id)
        log.info("New session id: {id} for user {name}".format(id=self._session_id, name=current_user.name))

    def _new_session(self, user_id: str):
        session = WebsocketSession(send_cb=self._send)
        self._args.message_bus.subscribe(session, topic_user_requests(user_id))
        self._args.message_bus.subscribe(session, topic_user_updates(user_id))
        self.sessions[self._session_id] = session

    def on_close(self):
        current_user = self.current_user
        self._remove_session()
        log.info("Closed session id: {id} for user {name}".format(id=self._session_id, name=current_user.name))

    def _remove_session(self):
        session_id = self._session_id
        if session_id in self.sessions:
            session = self.sessions[session_id]
            self._args.message_bus.unsubscribe_all(session)
            del self.sessions[session_id]
        else:
            log.error("Failed to remove session, no session found with id {id}".format(id=self._session_id))

    def _send(self, msg: Message):
        data = self._args.message_protocol.encode(msg)
        if data:
            self._try_send(data)
            log.debug("Sending message to {name} on session {id}".format(
                name=self.current_user.name,
                id=self._session_id
            ))
        else:
            log.error("Failed to encode received message from message bus")

    def _try_send(self, data: str):
        try:
            self.write_message(data)
        except tornado.websocket.WebSocketClosedError:
            log.error("Failed to send message: websocket is closed")

    def on_message(self, data):
        try:
            message = self._args.message_protocol.decode(data)
            self._forward_message(message)
            log.debug("Forward received message from {name} on session {id}".format(
                name=self.current_user.name,
                id=self._session_id
            ))
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
