import unittest
from unittest.mock import Mock
import urllib.parse

from tornado.testing import AsyncHTTPTestCase
import tornado.web
import tornado.escape
import tornado.httputil

from application import (
    User,
    UnprivilegedUser
)
from .user_account_password import (
    Parameter,
    UserAccountPasswordLogin,
    UserAccountPasswordLogout,
)
from application import (
    UserAccountAuthentication
)
from .base import AUTH_TOKEN_NAME
from stubs import UserSerializerStub


valid_user = User(id_="123-456-789", name="user", privilege=User.Privilege.USER)  # Used as reference representing a valid and authorized user during the tests (but not used in any assertion at the moment).


class TestUserAccountPassword(AsyncHTTPTestCase):
    API_BASE_URL = "/"
    API_ENDPOINT_LOGIN = "/auth/login"
    API_ENDPOINT_LOGOUT = "/auth/logout"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_auth = Mock(spec=UserAccountAuthentication)
        self._user_serializer_stub = UserSerializerStub()

    def setUp(self):
        super().setUp()
        self._user_auth.reset_mock()
        self._user_auth.authenticate.return_value = valid_user
        self._user_serializer_stub.set_response_data_for("unserialize", UnprivilegedUser())

    def get_app(self):
        return tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (self.API_ENDPOINT_LOGIN, UserAccountPasswordLogin, dict(
                    user_serializer=self._user_serializer_stub,
                    user_auth=self._user_auth,
                    app_base_url=self.API_BASE_URL
                )),
                (self.API_ENDPOINT_LOGOUT, UserAccountPasswordLogout, dict(
                    app_base_url=self.API_BASE_URL
                ))
            ]
        )

    def test_login_no_username_or_password_provided(self):
        response = self.fetch(self.API_ENDPOINT_LOGIN, method="POST", body="")
        self.assertEqual(400, response.code)

    def test_login_only_username_provided(self):
        response = self.fetch(
            self.API_ENDPOINT_LOGIN,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.USERNAME: valid_user.name
            })
        )
        self.assertEqual(400, response.code)

    def test_login_only_password_provided(self):
        response = self.fetch(
            self.API_ENDPOINT_LOGIN,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.PASSWORD: "secret"
            })
        )
        self.assertEqual(400, response.code)

    def test_login_password_and_username_provided(self):
        response = self.fetch(
            self.API_ENDPOINT_LOGIN,
            method="POST",
            follow_redirects=False,
            body=urllib.parse.urlencode({
                Parameter.USERNAME: valid_user.name,
                Parameter.PASSWORD: "secret"
            })
        )
        self.assertEqual(302, response.code)
        self.assertIn("Location", response.headers)

    def test_login_when_user_unauthorized(self):
        self._user_auth.authenticate.return_value = UnprivilegedUser()
        response = self.fetch(
            self.API_ENDPOINT_LOGIN,
            method="POST",
            follow_redirects=False,
            body=urllib.parse.urlencode({
                Parameter.USERNAME: "not" + valid_user.name,
                Parameter.PASSWORD: "secret"
            })
        )
        self.assertEqual(401, response.code)

    def test_login_set_cookie_on_success(self):
        response = self.fetch(
            self.API_ENDPOINT_LOGIN,
            method="POST",
            follow_redirects=False,
            body=urllib.parse.urlencode({
                Parameter.USERNAME: valid_user.name,
                Parameter.PASSWORD: "secret"
            })
        )
        self.assertRegex(
            response.headers.get("Set-Cookie"),
            "^{cookie_name}=\"?.+\"?".format(cookie_name=AUTH_TOKEN_NAME)
        )

    def test_login_redirect_to_next(self):
        next_path = "/path/to/next"
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGIN, dict(next=next_path))
        response = self.fetch(
            url,
            method="POST",
            follow_redirects=False,
            body=urllib.parse.urlencode({
                Parameter.USERNAME: valid_user.name,
                Parameter.PASSWORD: "secret"
            })
        )
        self.assertEqual(302, response.code)
        self.assertEqual(response.headers.get("Location"), next_path)

    def test_login_redirect_when_already_logged_in(self):
        next_path = "/path/to/next"
        self._user_serializer_stub.set_response_data_for("unserialize", valid_user)  # user is authenticated
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGIN, dict(next=next_path))
        response = self.fetch(
            url,
            method="POST",
            follow_redirects=False,
            body=urllib.parse.urlencode({
                Parameter.USERNAME: valid_user.name,
                Parameter.PASSWORD: "secret"
            })
        )
        self._user_auth.authenticate.assert_not_called()
        self.assertEqual(302, response.code)
        self.assertEqual(response.headers.get("Location"), next_path)

    def test_login_redirect_to_default_url(self):
        response = self.fetch(
            self.API_ENDPOINT_LOGIN,
            method="POST",
            follow_redirects=False,
            body=urllib.parse.urlencode({
                Parameter.USERNAME: valid_user.name,
                Parameter.PASSWORD: "secret"
            })
        )
        self.assertEqual(302, response.code)
        self.assertEqual(response.headers.get("Location"), self.API_BASE_URL)

    def test_logout_clear_cookie(self):
        logout_response = self.fetch(
            self.API_ENDPOINT_LOGOUT,
            method="GET",
            follow_redirects=False
        )
        self.assertRegex(
            logout_response.headers["Set-Cookie"],
            "^{cookie_name}=\"\"".format(cookie_name=AUTH_TOKEN_NAME)
        )

    def test_logout_redirect_to_next(self):
        next_path = "/path/to/next"
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGOUT, dict(next=next_path))
        response = self.fetch(
            url,
            method="GET",
            follow_redirects=False
        )
        self.assertEqual(302, response.code)
        self.assertEqual(response.headers.get("Location"), next_path)

    def test_logout_redirect_to_default_url(self):
        response = self.fetch(
            self.API_ENDPOINT_LOGOUT,
            method="GET",
            follow_redirects=False
        )
        self.assertEqual(302, response.code)
        self.assertEqual(response.headers.get("Location"), self.API_BASE_URL)


if __name__ == "__main__":
    unittest.main()
