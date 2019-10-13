from .endpoints import (
    OpenIDEndpoints,
)


class OpenIDClientConfiguration:

    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def client_secret(self) -> str:
        return self._client_secret


class OpenIDConfiguration:

    """ Data structure aggregating all openid configurations """

    def __init__(self, endpoints: OpenIDEndpoints, client_config: OpenIDClientConfiguration):
        self._endpoints = endpoints
        self._client_config = client_config

    @property
    def endpoints(self) -> OpenIDEndpoints:
        return self._endpoints

    @property
    def client_config(self) -> OpenIDClientConfiguration:
        return self._client_config
