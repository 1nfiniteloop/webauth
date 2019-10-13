import urllib.parse

from http_client import (
    AsyncHttpClient,
)
from .token_request import (
    TokenFromCodeExchangeBuilder,
    TokenFromCodeExchanger,
    TokenFromCodeHttpExchanger,
    TokenHttpRequest
)
from .configuration import OpenIDClientConfiguration


class GoogleTokenHttpRequest(TokenHttpRequest):

    def __init__(self, openid_client_config: OpenIDClientConfiguration, callback_url: str):
        self._openid_client_config = openid_client_config
        self._callback_url = callback_url

    def header(self) -> dict:
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        return header

    def body(self, code: str) -> str:
        body = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._callback_url,
            "client_id": self._openid_client_config.client_id,
            "client_secret": self._openid_client_config.client_secret
        })
        return body


class GoogleTokenFromCodeExchangeBuilder(TokenFromCodeExchangeBuilder):

    def __init__(self, http_client: AsyncHttpClient):
        self._http_client = http_client

    def new(self, token_endpoint: str, openid_client_config: OpenIDClientConfiguration, callback_url: str) -> TokenFromCodeExchanger:
        id_token_request = TokenFromCodeHttpExchanger(
            self._http_client,
            token_endpoint,
            GoogleTokenHttpRequest(openid_client_config, callback_url)
        )
        return id_token_request
