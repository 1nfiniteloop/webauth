import base64
import urllib.parse

import tornado.escape

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


def encode_authorization_token(client_id: str, client_secret: str) -> str:
    token = "{client_id}:{client_secret}".format(
        client_id=client_id,
        client_secret=client_secret
    )
    return base64.b64encode(token.encode("utf8")).decode("utf8")


def json_decode(data: str):
    return tornado.escape.json_decode(data)


class KeycloakTokenHttpRequest(TokenHttpRequest):

    def __init__(self, openid_client_config: OpenIDClientConfiguration, callback_url: str):
        self._openid_client_config = openid_client_config
        self._callback_url = callback_url

    def header(self) -> dict:
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic {authorization_token}".format(
                authorization_token=encode_authorization_token(
                    self._openid_client_config.client_id,
                    self._openid_client_config.client_secret
                )
            )
        }
        return header

    def body(self, code: str) -> str:
        body = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._callback_url,
        })
        return body


class KeycloakTokenFromCodeExchangeBuilder(TokenFromCodeExchangeBuilder):

    def __init__(self, http_client: AsyncHttpClient):
        self._http_client = http_client

    def new(self, token_endpoint: str, openid_client_config: OpenIDClientConfiguration, callback_url: str) -> TokenFromCodeExchanger:
        id_token_request = TokenFromCodeHttpExchanger(
            self._http_client,
            token_endpoint,
            KeycloakTokenHttpRequest(openid_client_config, callback_url)
        )
        return id_token_request
