from abc import (
    ABC,
    abstractmethod
)
from datetime import (
    datetime,
    timedelta
)
import logging
from typing import (
    Any,
    List,
    Callable
)

from application import (
    Host
)
from application.messaging import MessageBus
from application.storage import (
    HostStorage,
    UnixAccountStorage
)
from messaging import (
    SendPolicy,
    Request,
    ResponseCallback
)

from .messages import (
    AuthorizationRequestMessage,
    AuthorizationResponseMessage,
    AuthorizationUpdateMessage
)
from .state import AuthorizationState
from .topics import (
    topic_user_requests,
    topic_user_responses,
    topic_user_updates
)

log = logging.getLogger(__name__)


class AuthorizationRequestSubject:

    """ The subject for authorization requests (what to authorize, which context?) """

    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(self, host_id: str, unix_account_id: int, service_name: str, timeout: int = DEFAULT_TIMEOUT):
        self._host_id = host_id
        self._unix_account_id = unix_account_id
        self._service_name = service_name
        self._expires = datetime.now() + timedelta(seconds=timeout)

    @property
    def host_id(self) -> str:
        return self._host_id

    @property
    def unix_account_id(self) -> int:
        return self._unix_account_id

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def expires(self) -> datetime:
        return self._expires


class AuthorizationResponse:

    def __init__(self, response_code: AuthorizationState, message: str = ""):
        self._response_code = response_code
        self._message = message

    @property
    def state(self) -> AuthorizationState:
        return self._response_code

    @property
    def message(self) -> str:
        return self._message


class Response:

    """ This object contains the response """

    def __init__(self):
        self._response = AuthorizationResponse(AuthorizationState.WAITING)

    def set_state_authorized(self):
        self._response = AuthorizationResponse(AuthorizationState.AUTHORIZED)

    def set_state_unauthorized(self):
        self._response = AuthorizationResponse(AuthorizationState.UNAUTHORIZED)

    def set_state_expired(self):
        self._response = AuthorizationResponse(AuthorizationState.EXPIRED)

    def set_state_error(self, error_text: str):
        self._response = AuthorizationResponse(
            AuthorizationState.ERROR,
            error_text
        )

    def get_message(self) -> AuthorizationResponse:
        return self._response


class AuthorizationResponseCallback(ResponseCallback):

    def __init__(self, response: Response, on_expired_cb: Callable[[], Any]):
        self._response = response
        self._on_expired_cb = on_expired_cb

    def on_response(self, msg: AuthorizationResponseMessage):
        if msg.state == AuthorizationState.AUTHORIZED:
            self._response.set_state_authorized()
        elif msg.state == AuthorizationState.UNAUTHORIZED:
            self._response.set_state_unauthorized()
        else:
            error_text = "Received unknown state: {name}".format(name=msg.state.name)
            log.error(error_text)
            self._response.set_state_error(error_text)

    def on_expired(self):
        self._response.set_state_expired()
        self._on_expired_cb()


class AuthorizationRequestBuilder(ABC):

    @abstractmethod
    def new(self, msg_bus: MessageBus, users_id: List[str], response_cb: ResponseCallback) -> Request:
        pass


class DefaultAuthorizationRequestBuilder(AuthorizationRequestBuilder):

    def new(self, msg_bus: MessageBus, users_id: List[str], response_cb: ResponseCallback) -> Request:
        request = Request(
            msg_bus,
            response_cb,
            self._get_request_topics(users_id),
            self._get_response_topics(users_id),
            policy=SendPolicy.AT_LEAST_ONE
        )
        return request

    @staticmethod
    def _get_request_topics(users_id: List[str]) -> List[str]:
        return list(topic_user_requests(id_) for id_ in users_id)

    @staticmethod
    def _get_response_topics(users_id: List[str]) -> List[str]:
        return list(topic_user_responses(id_) for id_ in users_id)


class AuthorizationRequest(ABC):

    @abstractmethod
    async def authorize(self, subject: AuthorizationRequestSubject) -> AuthorizationResponse:
        pass


class UnixAccountAuthorizationRequest(AuthorizationRequest):

    """ This is used to authenticate user, host and authorize the request """

    def __init__(self, msg_bus: MessageBus, unix_account_storage: UnixAccountStorage, host_storage: HostStorage, request_builder: AuthorizationRequestBuilder):
        self._msg_bus = msg_bus
        self._unix_account_storage = unix_account_storage
        self._host_storage = host_storage
        self._request_builder = request_builder

    async def authorize(self, subject: AuthorizationRequestSubject) -> AuthorizationResponse:
        response = Response()
        host = self._get_host(subject.host_id)
        users_id = self._get_users_id(subject.unix_account_id)
        if not host.id:
            response.set_state_error("Host with id '{id}' not found".format(id=subject.host_id))
        elif not users_id:
            response.set_state_error("No users found associated with unix account id '{id}'".format(
                id=subject.unix_account_id
            ))
        else:
            message = AuthorizationRequestMessage(
                self._get_unix_account_name(subject.unix_account_id),
                host.name,
                subject.service_name,
            )
            response_cb = self._create_response_callback(users_id, message.id, response)
            request = self._request_builder.new(
                self._msg_bus,
                users_id,
                response_cb
            )
            send_success = await request.send(message, subject.expires)
            if not send_success:
                response.set_state_error("Failed to send request (no receivers available)")
        return response.get_message()

    def _get_host(self, host_id: str) -> Host:
        return self._host_storage.get_host_by_id(host_id)

    def _get_users_id(self, unix_account_id: int) -> list:
        return self._unix_account_storage.get_associated_users_for_unix_account(unix_account_id)

    def _create_response_callback(self, users_id: List[str], request_id: str, response: Response) -> ResponseCallback:
        expired_cb = lambda: self._send_update_expired(users_id, request_id)
        return AuthorizationResponseCallback(response, expired_cb)

    def _send_update_expired(self, users_id: List[str], request_id: str):
        msg = AuthorizationUpdateMessage(request_id, AuthorizationState.EXPIRED)
        for user_id in users_id:
            self._msg_bus.publish(topic_user_updates(user_id), msg)

    def _get_unix_account_name(self, unix_account_id: int) -> str:
        unix_account = self._unix_account_storage.get_unix_account_by_id(unix_account_id)
        return unix_account.name
