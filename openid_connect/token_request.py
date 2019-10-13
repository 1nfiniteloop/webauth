from abc import (
    ABC,
    abstractmethod
)
import json

import tornado.escape

from application import Credentials
from http_client import (
    AsyncHttpClient,
    HttpRequestFailed
)
from .configuration import OpenIDClientConfiguration


# How do we enforce that required keys are provided (dict type)?
class OpenIDTokenCredentials(Credentials):
    pass


class TokenRequestFailed(Exception):
    pass


class TokenFromCodeExchanger(ABC):

    @abstractmethod
    async def get_token_from_code(self, code: str) -> OpenIDTokenCredentials:
        pass


class TokenFromCodeExchangeBuilder(ABC):

    @abstractmethod
    def new(self, token_endpoint: str, openid_client_config: OpenIDClientConfiguration, callback_url: str) -> TokenFromCodeExchanger:
        pass


class TokenHttpRequest(ABC):

    @abstractmethod
    def body(self, code: str) -> str:
        pass

    @abstractmethod
    def header(self) -> dict:
        pass


class TokenFromCodeHttpExchanger(TokenFromCodeExchanger):

    """ Base class for fetching tokens using http request. The HTTP request sent is implemented in the derived class """

    def __init__(self, http_client: AsyncHttpClient, token_endpoint: str, http_request: TokenHttpRequest):
        self._http_client = http_client
        self._token_endpoint = token_endpoint
        self._http_request = http_request

    async def get_token_from_code(self, code: str) -> OpenIDTokenCredentials:
        response_body = await self._try_exchange_token(code)
        return self._try_decode_response(response_body)

    async def _try_exchange_token(self, code: str):
        try:
            return await self._http_client.post(
                self._token_endpoint,
                body=self._http_request.body(code),
                header=self._http_request.header()
            )
        except HttpRequestFailed as err:
            raise TokenRequestFailed(err)

    def _try_decode_response(self, response_body: str) -> OpenIDTokenCredentials:
        try:
            return json_decode(response_body)
        except json.decoder.JSONDecodeError:
            raise TokenRequestFailed("Could not decode response into JSON from token endpoint: \"{response}\"".format(
                response=response_body
            ))


def json_decode(data: str):
    return tornado.escape.json_decode(data)
