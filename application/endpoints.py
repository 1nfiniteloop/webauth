from abc import (
    ABC,
    abstractmethod
)
from typing import (
    Dict
)

class OpenIDProviderEndpoint:

    def __init__(self, name: str, login: str, logout: str, register: str):
        self._name = name
        self._login = login
        self._logout = logout
        self._register = register

    @property
    def name(self):
        return self._name

    @property
    def login(self) -> str:
        return self._login

    @property
    def logout(self) -> str:
        return self._logout

    @property
    def register(self) -> str:
        return self._register


class AdministrationEndpoints:

    def __init__(self, hosts: str, user_accounts: str, unix_accounts: str):
        self._hosts = hosts
        self._user_accounts = user_accounts
        self._unix_accounts = unix_accounts

    @property
    def hosts(self) -> str:
        return self._hosts

    @property
    def user_accounts(self) -> str:
        return self._user_accounts

    @property
    def unix_accounts(self) -> str:
        return self._unix_accounts


class BackChannelEndpoints:

    def __init__(self, authorization: str):
        self._authorization = authorization

    @property
    def authorization(self) -> str:
        return self._authorization


class UserEndpoints:

    def __init__(self, api_endpoints: str, user_registration: str, websocket: str, websocket_url: str, logout: str, openid_providers: Dict[str, OpenIDProviderEndpoint] = None):
        self._api_endpoints = api_endpoints
        self._user_registration = user_registration
        self._websocket = websocket
        self._websocket_url = websocket_url
        self._logout = logout
        self._openid_providers = openid_providers

    @property
    def api_endpoints(self) -> str:
        return self._api_endpoints

    @property
    def user_registration(self) -> str:
        return self._user_registration

    @property
    def websocket(self) -> str:
        return self._websocket


    @property
    def websocket_url(self) -> str:
        return self._websocket_url

    @property
    def logout(self) -> str:
        return self._logout

    @property
    def openid_providers(self) -> Dict[str, OpenIDProviderEndpoint]:
        return self._openid_providers


class UserEndpointsSerializer(ABC):

    @abstractmethod
    def serialize(self, endpoints: UserEndpoints) -> str:
        pass
