import asyncio
import unittest
from unittest.mock import Mock
import json

from .token_request import (
    TokenFromCodeHttpExchanger,
    TokenHttpRequest,
    TokenRequestFailed
)
from http_client import (
    AsyncHttpClient,
    HttpRequestFailed
)

loop = asyncio.new_event_loop()
callback_url = "http://localhost:8080/login/callback"


class AsyncHttpClientStub(AsyncHttpClient):

    def __init__(self):
        self._response_body_fcn = self._default_response_fcn

    def _default_response_fcn(self):
        return ""

    def reset_mock(self):
        self._response_body_fcn = self._default_response_fcn

    def set_response_body_fcn(self, response_body_fcn):
        self._response_body_fcn = response_body_fcn

    async def get(self, url: str) -> str:
        return self._response_body_fcn()

    async def post(self, url: str, body: str, header: dict = None) -> str:
        return self._response_body_fcn()


def async_test(coro):
    def wrapper(*args, **kwargs):
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


class TestKeycloakOpenIDTokenRequest(unittest.TestCase):
    API_TOKEN_ENDPOINT = "/token_endpoint"
    CODE = "123-456-789"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._http_client_stub = AsyncHttpClientStub()

    def setUp(self):
        self._http_client_stub.reset_mock()

    @async_test
    async def test_response_not_json(self):
        self._http_client_stub.set_response_body_fcn(lambda: "not json")
        req = TokenFromCodeHttpExchanger(self._http_client_stub, self.API_TOKEN_ENDPOINT, Mock(spec=TokenHttpRequest))
        with self.assertRaisesRegex(TokenRequestFailed, "^Could not decode response into JSON.*"):
            tokens = await req.get_token_from_code(self.CODE)

    @async_test
    async def test_response_when_http_error(self):
        http_error = "Http Client Error"
        def response_fcn():
            raise HttpRequestFailed(http_error)
        self._http_client_stub.set_response_body_fcn(response_fcn)
        req = TokenFromCodeHttpExchanger(self._http_client_stub, self.API_TOKEN_ENDPOINT, Mock(spec=TokenHttpRequest))
        with self.assertRaisesRegex(TokenRequestFailed, http_error):
            tokens = await req.get_token_from_code(self.CODE)

    @async_test
    async def test_response_containing_tokens(self):
        expected_tokens = {"id_token": "...", "refresh_token": "..."}
        self._http_client_stub.set_response_body_fcn(lambda: json.dumps(expected_tokens))
        req = TokenFromCodeHttpExchanger(self._http_client_stub, self.API_TOKEN_ENDPOINT, Mock(spec=TokenHttpRequest))
        tokens = await req.get_token_from_code(self.CODE)
        self.assertEqual(tokens, expected_tokens)
