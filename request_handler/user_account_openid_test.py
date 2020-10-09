from unittest.mock import Mock
import urllib.parse

from tornado.testing import AsyncHTTPTestCase
import tornado.web
import tornado.escape
import tornado.httputil

from application import (
    User,
    UnprivilegedUser,
    UserAccountAuthentication,
    UserAccountRegistration
)
from openid_connect import (
    OpenIDClientConfiguration,
    TokenFromCodeExchanger,
    TokenRequestFailed,
    JwtDecodeFailed
)
from storage import UniqueConstraintFailed
from stubs import UserSerializerStub

from .base import (
    AUTH_TOKEN_NAME,
    SESSION_TOKEN_NAME
)
from .user_account_openid import (
    OAuth2Authorization,
    OAuth2AuthorizationArguments,
    UserAccountLoginCallback,
    UserAccountRegistrationCallback,
    UserAccountLogoutOpenID
)


# Used as reference representing a valid and authorized user during the tests (but not used in any assertion at the moment).
valid_user = User(id_="123-456-789", name="user", privilege=User.Privilege.USER)


async def get_token_from_code(code: str) -> str:
    return "<raw-jwt>"

class TokenFromCodeExchangerStub(TokenFromCodeExchanger):

    async def get_token_from_code(self, code: str) -> str:
        return "<raw-jwt>"


class TestOAuth2Authorization(AsyncHTTPTestCase):
    API_BASE_URL = "/"
    API_ENDPOINT_LOGIN = "/login"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_serializer_stub = UserSerializerStub()
        self._openid_client_config = OpenIDClientConfiguration("client-id", "client-secret")
        self._authorization_endpoint = "/authorization"

    def setUp(self):
        super().setUp()
        self._user_serializer_stub.set_response_data_for("unserialize", UnprivilegedUser())

    def get_app(self):
        args = OAuth2AuthorizationArguments(
            callback_url="/login/callback",
            app_base_path=self.API_BASE_URL,
            authorization_endpoint=self._authorization_endpoint,
            openid_client_id=self._openid_client_config.client_id
        )
        return tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (self.API_ENDPOINT_LOGIN, OAuth2Authorization, dict(
                    user_serializer=self._user_serializer_stub,
                    args=args
                )),
            ]
        )

    def test_login_redirect(self):
        """ Expects to be redirected to "authorization_endpoint"
        ref: https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest"""
        response = self.fetch(
            self.API_ENDPOINT_LOGIN,
            method="GET",
            follow_redirects=False,
        )
        location = response.headers.get("Location")
        redirect_url = urllib.parse.urlparse(location)
        self.assertEqual(302, response.code)
        self.assertEqual(redirect_url.path, self._authorization_endpoint)
        # assert parameters also?


class TestUserAccountLoginCallback(AsyncHTTPTestCase):
    API_BASE_URL = "/"
    API_ENDPOINT_LOGIN_CB = "/login/callback"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_serializer_stub = UserSerializerStub()
        self._user_auth = Mock(spec=UserAccountAuthentication)
        self._token_exchanger = Mock(spec=TokenFromCodeExchanger)

    def setUp(self):
        super().setUp()
        user = UnprivilegedUser()
        self._user_serializer_stub.set_response_data_for("unserialize", user)
        self._user_auth.reset_mock()
        self._user_auth.authenticate.return_value = user
        self._token_exchanger.get_token_from_code = get_token_from_code

    def get_app(self):
        return tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (self.API_ENDPOINT_LOGIN_CB, UserAccountLoginCallback, dict(
                    user_serializer=self._user_serializer_stub,
                    token_request=self._token_exchanger,
                    user_authentication=self._user_auth,
                    app_base_path=self.API_BASE_URL
                ))
            ]
        )

    def test_login_callback_when_authorization_endpoint_returns_error(self):
        """ ref: https://openid.net/specs/openid-connect-core-1_0.html#AuthError """
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGIN_CB, {
            "error": "bad_request",
            "error_description": "Unsupported response_type"
        })
        response = self.fetch(url, method="GET")
        self.assertEqual(400, response.code)

    def test_login_callback_when_incorrect_arguments_provided(self):
        """ ref: https://openid.net/specs/openid-connect-core-1_0.html#AuthError """
        url = self.API_ENDPOINT_LOGIN_CB
        response = self.fetch(url, method="GET")
        self.assertEqual(400, response.code)

    def test_login_callback_set_auth_token_cookie_on_success(self):
        self._user_auth.authenticate.return_value = valid_user
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGIN_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertRegex(
            response.headers.get("Set-Cookie"),
            "{cookie_name}=\"?.+\"?".format(cookie_name=AUTH_TOKEN_NAME)
        )

    def test_login_callback_set_user_session_cookie_on_success(self):
        self._user_auth.authenticate.return_value = valid_user
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGIN_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertRegex(
            response.headers.get("Set-Cookie"),
            "{cookie_name}=\"?.+\"?".format(cookie_name=SESSION_TOKEN_NAME)
        )

    def test_login_callback_redirect_on_success(self):
        self._user_auth.authenticate.return_value = valid_user
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGIN_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        location = response.headers.get("Location")
        redirect_url = urllib.parse.urlparse(location)
        expected_redirect_url = self.API_BASE_URL
        self.assertEqual(302, response.code)
        self.assertEqual(redirect_url.path, expected_redirect_url)

    def test_login_callback_on_authenticate_fail(self):
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGIN_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertEqual(401, response.code)

    def test_login_user_with_nonvalid_jwt(self):
        self._user_auth.authenticate.side_effect = JwtDecodeFailed()
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGIN_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertEqual(400, response.code)

    def test_login_user_when_token_request_failed(self):
        self._user_auth.authenticate.side_effect = TokenRequestFailed()
        url = tornado.httputil.url_concat(self.API_ENDPOINT_LOGIN_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertEqual(400, response.code)


class TestUserAccountLogoutOpenID(AsyncHTTPTestCase):
    API_BASE_URL = "/"
    API_ENDPOINT_LOGOUT = "/logout"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_app(self):
        return tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (self.API_ENDPOINT_LOGOUT, UserAccountLogoutOpenID, dict(
                    openid_logout_endpoint=self.API_ENDPOINT_LOGOUT,
                    callback_url=self.API_BASE_URL
                ))
            ]
        )

    def test_logout_redirect_to_next(self):
        response = self.fetch(self.API_ENDPOINT_LOGOUT, method="GET", follow_redirects=False)
        location = response.headers.get("Location")
        redirect_url = urllib.parse.urlparse(location)
        expected_redirect_url = self.API_ENDPOINT_LOGOUT
        self.assertEqual(302, response.code)
        self.assertEqual(redirect_url.path, expected_redirect_url)

    def test_logout_clear_auth_token_cookie(self):
        response = self.fetch(self.API_ENDPOINT_LOGOUT, method="GET", follow_redirects=False)
        self.assertRegex(
            response.headers.get("Set-Cookie"),
            "{cookie_name}=\"\";".format(cookie_name=AUTH_TOKEN_NAME)
        )

    def test_logout_clear_user_session_cookie(self):
        response = self.fetch(self.API_ENDPOINT_LOGOUT, method="GET", follow_redirects=False)
        self.assertRegex(
            response.headers.get("Set-Cookie"),
            "{cookie_name}=\"\";".format(cookie_name=SESSION_TOKEN_NAME)
        )

class TestUserAccountRegistrationCallback(AsyncHTTPTestCase):
    API_BASE_URL = "/"
    API_REGISTER_CB = "/register/callback"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_serializer = UserSerializerStub()
        self._user_registration = Mock(spec=UserAccountRegistration)
        self._token_exchanger = Mock(spec=TokenFromCodeExchanger)

    def setUp(self):
        super().setUp()
        self.reset_mocks()

    def reset_mocks(self):
        user = UnprivilegedUser()
        self._user_serializer.set_response_data_for("unserialize", user)
        self._user_registration.reset_mock()
        self._user_registration.register_user.return_value = user
        self._user_registration.register_identity.return_value = False
        self._token_exchanger.reset_mock()
        self._token_exchanger.get_token_from_code = get_token_from_code

    def get_app(self):
        return tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (self.API_REGISTER_CB, UserAccountRegistrationCallback, dict(
                    user_serializer=self._user_serializer,
                    token_request=self._token_exchanger,
                    user_registration=self._user_registration,
                    app_base_path=self.API_BASE_URL
                ))
            ]
        )

    def test_register_callback_when_authorization_endpoint_returns_error(self):
        """ ref: https://openid.net/specs/openid-connect-core-1_0.html#AuthError """
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {
            "error": "bad_request",
            "error_description": "Unsupported response_type"
        })
        response = self.fetch(url, method="GET")
        self.assertEqual(400, response.code)

    def test_register_callback_when_incorrect_arguments_provided(self):
        """ ref: https://openid.net/specs/openid-connect-core-1_0.html#AuthError """
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {
            "asd": "123"
        })
        response = self.fetch(url, method="GET")
        self.assertEqual(400, response.code)

    def test_register_new_user_redirect_on_success(self):
        self._user_registration.register_identity.return_value = True
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        location = response.headers.get("Location")
        redirect_url = urllib.parse.urlparse(location)
        expected_redirect_url = self.API_BASE_URL
        self.assertEqual(302, response.code)
        self.assertEqual(redirect_url.path, expected_redirect_url)

    def test_register_new_user_set_cookie_on_success(self):
        self._user_registration.register_identity.return_value = True
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertRegex(
            response.headers.get("Set-Cookie"),
            "^{cookie_name}=\"?.+\"?".format(cookie_name=AUTH_TOKEN_NAME)
        )

    def test_register_user_with_non_unique_identity(self):
        self._user_registration.register_user.side_effect = UniqueConstraintFailed()
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertEqual(400, response.code)

    def test_register_user_with_nonvalid_jwt(self):
        self._user_registration.register_user.side_effect = JwtDecodeFailed()
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertEqual(400, response.code)

    def test_register_user_when_token_request_failed(self):
        self._user_registration.register_user.side_effect = TokenRequestFailed()
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertEqual(400, response.code)

    def test_register_new_user_and_non_unique_identity(self):
        self._user_serializer.set_response_data_for("unserialize", valid_user)  # a valid user session exists (user is logged in)
        self._user_registration.register_identity.return_value = False
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertEqual(400, response.code)

    def test_register_new_identity_on_existing_user(self):
        self._user_serializer.set_response_data_for("unserialize", valid_user)  # a valid user session exists (user is logged in)
        self._user_registration.register_identity.return_value = True
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        location = response.headers.get("Location")
        redirect_url = urllib.parse.urlparse(location)
        expected_redirect_url = self.API_BASE_URL
        self.assertEqual(302, response.code)
        self.assertEqual(redirect_url.path, expected_redirect_url)

    def test_register_non_unique_identity_on_existing_user(self):
        self._user_serializer.set_response_data_for("unserialize", valid_user)  # a valid user session exists (user is logged in)
        self._user_registration.register_identity.return_value = False
        url = tornado.httputil.url_concat(self.API_REGISTER_CB, {"code": "12345"})
        response = self.fetch(url, method="GET", follow_redirects=False)
        self.assertEqual(400, response.code)

