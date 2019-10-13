import uuid

from application.messaging import Message
from .state import AuthorizationState


class AuthorizationRequestMessage(Message):

    def __init__(self, unix_account_name: str, host_name: str, service_name: str):
        self._request_id = str(uuid.uuid4())
        self._unix_account_name = unix_account_name
        self._host_name = host_name
        self._service_name = service_name

    @property
    def id(self) -> str:
        return self._request_id

    @property
    def unix_account_name(self) -> str:
        return self._unix_account_name

    @property
    def host_name(self)  -> str:
        return self._host_name

    @property
    def service_name(self) -> str:
        return self._service_name


class AuthorizationResponseMessage(Message):

    def __init__(self, request_id: str, state: AuthorizationState):
        self._request_id = request_id
        self._state = state

    @property
    def id(self) -> str:
        return self._request_id

    @property
    def state(self) -> AuthorizationState:
        return self._state


class AuthorizationUpdateMessage(Message):

    def __init__(self, request_id: str, state: AuthorizationState):
        self._request_id = request_id
        self._state = state

    @property
    def id(self) -> str:
        return self._request_id

    @property
    def state(self) -> AuthorizationState:
        return self._state

