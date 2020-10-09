from unittest.mock import (
    Mock,
)

from tornado.testing import AsyncHTTPTestCase
import tornado.httputil
import tornado.web

from application import (
    User,
    UnprivilegedUser
)
from application.storage import (
    UserAccountActivationStorage,
    NonExistingUser
)
from .base import AUTH_TOKEN_NAME
from .user_account_activation import (
    UserAccountActivation,
    UserAccountActivationArguments
)
from stubs import (
    UserSerializerStub,
)


valid_user = User(id_="123-456-789", name="user", privilege=User.Privilege.USER)


def url_concat(base_url: str, args: dict):
    url = tornado.httputil.url_concat(
        base_url,
        args
    )
    return url


class TestUserAccountActivation(AsyncHTTPTestCase):
    API_ENDPOINT = "/user_account/new/{nonce}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_serializer = UserSerializerStub()
        self._storage = Mock(spec=UserAccountActivationStorage)

    def setUp(self):
        super().setUp()
        self._user_serializer.set_response_data_for("serialize", "serialized-user")
        self._storage.reset_mock()
        self._storage.pop_user.return_value = valid_user

    def _get_default_url(self):
        url = url_concat(
            self.API_ENDPOINT.format(nonce="1234-5678"),
            {"next": "/google/login"},
        )
        return url

    def get_app(self):
        args = UserAccountActivationArguments(
            self._user_serializer,
            self._storage,
        )
        request_url = self.API_ENDPOINT.format(nonce="(.*)")
        application = tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (request_url, UserAccountActivation, dict(args=args)),
            ])
        return application

    def test_nonce_not_provided(self):
        self._storage.pop_user.return_value = NonExistingUser()
        response = self.fetch(self._get_default_url(), method="GET")
        self.assertEqual(400, response.code)

    def test_when_argument_for_next_missing(self):
        url = self.API_ENDPOINT.format(nonce="1234-5678")
        response = self.fetch(url, method="GET")
        self.assertEqual(400, response.code)

    def test_when_nonce_missing(self):
        url = self.API_ENDPOINT.format(nonce="")
        response = self.fetch(url, method="GET")
        self.assertEqual(400, response.code)

    def test_set_cookie_on_success(self):
        response = self.fetch(self._get_default_url(), method="GET", follow_redirects=False)
        self.assertRegex(
            response.headers.get("Set-Cookie"),
            "^{cookie_name}=\"?.+\"?".format(cookie_name=AUTH_TOKEN_NAME)
        )

    def test_redirect_on_success(self):
        next_path = "/login/google"
        url = url_concat(
            self.API_ENDPOINT.format(nonce="1234-5678"),
            {"next": next_path},
        )
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertEqual(302, response.code)
        self.assertEqual(response.headers.get("Location"), next_path)
