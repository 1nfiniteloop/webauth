import unittest
import urllib.parse

from tornado.testing import AsyncHTTPSTestCase
import tornado.web

from .unix_account_authorization import (
    UnixAccountAuthorization,
    Parameter
)
from unix_account_authorization import (
    AuthorizationRequest,
    AuthorizationRequestSubject,
    AuthorizationResponse,
    AuthorizationState,
)
from stubs import StubResponseMixin


class AuthorizationRequestStub(AuthorizationRequest, StubResponseMixin):

    def __init__(self):
        super().__init__()

    def default_response_data(self) -> dict:
        response_data = {
            "authorize": AuthorizationResponse(AuthorizationState.AUTHORIZED)
        }
        return response_data

    async def authorize(self, subject: AuthorizationRequestSubject) -> AuthorizationResponse:
        return self.get_response()


class TestUnixAccountAuthorization(AsyncHTTPSTestCase):
    API_ENDPOINT = "/api/auth"
    
    def setUp(self):
        super().setUp()
        self._auth_request.reset_stub()

    def __init__(self, *args, **kwargs):
        self._auth_request = AuthorizationRequestStub()
        super().__init__(*args, **kwargs)

    def get_app(self):
        return tornado.web.Application(
            handlers=[
                (self.API_ENDPOINT, UnixAccountAuthorization, dict(auth=self._auth_request))
            ]
        )

    def test_no_parameters_sent(self):
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=""
        )
        self.assertEqual(400, response.code)

    def test_only_unix_account_id_sent(self):
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_ID: "123",
            })
        )
        self.assertEqual(400, response.code)

    def test_non_numeric_unix_account_id(self):
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_ID: "non-numeric",
                Parameter.SERVICE: "login"
            })
        )
        self.assertEqual(400, response.code)

    def test_all_required_parameters_sent_and_request_approved(self):
        self._auth_request.set_response_data_for("authorize", AuthorizationResponse(AuthorizationState.AUTHORIZED))
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_ID: "1000",
                Parameter.SERVICE: "login"
            })
        )
        self.assertEqual(200, response.code)

    def test_request_denied(self):
        self._auth_request.set_response_data_for("authorize", AuthorizationResponse(AuthorizationState.UNAUTHORIZED))
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_ID: "1000",
                Parameter.SERVICE: "login"
            })
        )
        self.assertEqual(401, response.code)

    def test_request_timeout(self):
        self._auth_request.set_response_data_for("authorize", AuthorizationResponse(AuthorizationState.EXPIRED))
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_ID: "1000",
                Parameter.SERVICE: "login"
            })
        )
        self.assertEqual(408, response.code)

    def test_other_error(self):
        self._auth_request.set_response_data_for(
            "authorize",
            AuthorizationResponse(AuthorizationState.ERROR, "Something else went wrong")
        )
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_ID: "1000",
                Parameter.SERVICE: "login"
            })
        )
        self.assertEqual(400, response.code)


if __name__ == "__main__":
    unittest.main()
