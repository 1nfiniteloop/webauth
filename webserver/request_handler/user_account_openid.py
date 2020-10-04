import logging
from tornado.auth import (
    OAuth2Mixin
)
import tornado.web
import tornado.httputil
import base64

from application import (
    User,
    UserAccountAuthentication,
    UserAccountRegistration,
    Credentials
)
from .base import (
    AUTH_TOKEN_NAME,
    SESSION_TOKEN_NAME,
    AuthenticatedUserBase
)
from user_serializer import (
    UserSerializer,
)
from openid_connect import (
    TokenFromCodeExchanger,
    TokenRequestFailed,
    JwtDecodeFailed
)

from storage import UniqueConstraintFailed

log = logging.getLogger(__name__)


class Parameter:
    """ String literals (don't repeat yoursself) """
    CODE, REDIRECT_URI, ERROR, ERROR_DESCRIPTION = "code", "rederct_uri", "error", "error_description"


class OAuth2AuthorizationArguments:

    """ Data structure for http handler """

    def __init__(self, callback_url: str, app_base_path: str, authorization_endpoint: str, openid_client_id: str):
        self._callback_url = callback_url
        self._app_base_path = app_base_path
        self._authorization_endpoint = authorization_endpoint
        self._openid_client_id = openid_client_id

    @property
    def callback_url(self) -> str:
        return self._callback_url

    @property
    def app_base_path(self) -> str:
        return self._app_base_path

    @property
    def authorization_endpoint(self) -> str:
        return self._authorization_endpoint

    @property
    def openid_client_id(self) -> str:
        return self._openid_client_id


class OAuth2Authorization(AuthenticatedUserBase, OAuth2Mixin):

    """ https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest """

    def initialize(self, user_serializer: UserSerializer, args: OAuth2AuthorizationArguments):
        self._user_serializer = user_serializer
        self._args = args
        # attributes required from the mixin classes:
        self._OAUTH_AUTHORIZE_URL = args.authorization_endpoint

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._user_serializer.unserialize(client_cookie)

    def get(self):
        self.authorize_redirect(
            self._args.callback_url,
            client_id=self._args.openid_client_id,
            response_type=Parameter.CODE,
            scope=["openid", "profile"]
        )


class UserAccountLoginCallback(AuthenticatedUserBase, OAuth2Mixin):

    """ Ref: https://openid.net/specs/openid-connect-core-1_0.html#TokenRequest """

    def initialize(self, user_serializer: UserSerializer, token_request: TokenFromCodeExchanger, user_authentication: UserAccountAuthentication, app_base_path: str):
        self._user_serializer = user_serializer
        self._token_request = token_request
        self._user_authentication = user_authentication
        self._app_base_path = app_base_path

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._user_serializer.unserialize(client_cookie)

    def serialize_auth_token(self, user: User) -> str:
        return self._user_serializer.serialize(user)

    def serialize_user_session(self, user: User) -> bytes:
        return base64.b64encode(bytes(self.serialize_auth_token(user), encoding="utf8"))

    async def get(self):
        if Parameter.CODE in self.request.arguments:
            authenticated = False
            code = self.get_argument(Parameter.CODE)
            try:
                authenticated = await self._try_authenticate_user(code)
                if authenticated:
                    self.redirect(self._app_base_path)
                else:
                    self.send_error(401, reason="User is unauthorized")
            except TokenRequestFailed as err:
                self.send_error(400, reason="User registration failed")
                log.error("User registration failed: {err}".format(err=err))
            except JwtDecodeFailed as err:
                self.send_error(400, reason="Failed to decode JWT")
                log.error("Failed to decode JWT: {err}".format(err=err))
        elif Parameter.ERROR in self.request.arguments:
            error = self.get_argument(Parameter.ERROR)
            error_description = self.get_argument(Parameter.ERROR_DESCRIPTION)
            self.send_error(400, reason="{error}: {description}".format(error=error, description=error_description))
        else:
            self.send_error(400, reason="Response does not contain \"code\" or \"error\"")

    async def _try_authenticate_user(self, code: str) -> bool:
        openid_credentials = await self._token_request.get_token_from_code(code)
        user = self._user_authentication.authenticate(openid_credentials)
        return self._authenticate_user(user)

    def _authenticate_user(self, user: User) -> bool:
        authenticated = False
        if user.privilege.value:  # != User.Privilege.NONE:
            self.set_secure_cookie(AUTH_TOKEN_NAME, self.serialize_auth_token(user))
            self.set_cookie(SESSION_TOKEN_NAME, self.serialize_user_session(user))
            authenticated = True
        return authenticated

class UserAccountRegistrationCallback(AuthenticatedUserBase, OAuth2Mixin):

    """ Ref: https://openid.net/specs/openid-connect-core-1_0.html#TokenRequest """

    def initialize(self, user_serializer: UserSerializer, token_request: TokenFromCodeExchanger, user_registration: UserAccountRegistration, app_base_path: str):
        self._user_serializer = user_serializer
        self._token_request = token_request
        self._user_registration = user_registration
        self._app_base_path = app_base_path

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._user_serializer.unserialize(client_cookie)

    def serialize_auth_token(self, user: User) -> str:
        return self._user_serializer.serialize(user)

    def serialize_user_session(self, user: User) -> bytes:
        return base64.b64encode(bytes(self.serialize_auth_token(user), encoding="utf8"))

    async def get(self):
        if Parameter.CODE in self.request.arguments:
            code = self.get_argument(Parameter.CODE)
            try:
                await self._try_register(code)
            except TokenRequestFailed as err:
                self.send_error(400, reason="User registration failed")
                log.error("User registration failed: {err}".format(err=err))
            except UniqueConstraintFailed as err:
                self.send_error(400, reason="Identity is already registered")
                log.error("Unique constraint failed: {err}".format(err=err))
            except JwtDecodeFailed as err:
                self.send_error(400, reason="Failed to decode JWT")
                log.error("Failed to decode JWT: {err}".format(err=err))
        elif Parameter.ERROR in self.request.arguments:
            error = self.get_argument(Parameter.ERROR)
            error_description = self.get_argument(Parameter.ERROR_DESCRIPTION)
            self.send_error(400, reason="{error}: {description}".format(error=error, description=error_description))
        else:
            self.send_error(400, reason="Response does not contain \"code\" or \"error\"")

    async def _try_register(self, code: str):
        openid_credentials = await self._token_request.get_token_from_code(code)
        if self.current_user.privilege.value:
            self._register_new_identity(openid_credentials)
        else:
            self._register_new_user(openid_credentials)

    def _register_new_identity(self, openid_credentials: Credentials):
        success = self._user_registration.register_identity(self.current_user, openid_credentials)
        if success:
            self.redirect(self._app_base_path)
        else:
            self.send_error(400, reason="Identity is already registred (or user not found)")

    def _register_new_user(self, openid_credentials: Credentials):
        user = self._user_registration.register_user(openid_credentials)
        self.set_secure_cookie(AUTH_TOKEN_NAME, self.serialize_auth_token(user))
        self.set_cookie(SESSION_TOKEN_NAME, self.serialize_user_session(user))
        self.redirect(self._app_base_path)


class UserAccountLogoutOpenID(tornado.web.RequestHandler):

    """ https://www.keycloak.org/docs/latest/securing_apps/index.html#logout-endpoint-2 """

    def initialize(self, openid_logout_endpoint: str, callback_url: str):
        self._openid_logout_endpoint = openid_logout_endpoint
        self._callback_url = callback_url

    def get(self):
        url = tornado.httputil.url_concat(
            self._openid_logout_endpoint,
            dict(redirect_uri=self._callback_url)
        )
        self.clear_cookie(AUTH_TOKEN_NAME)
        self.clear_cookie(SESSION_TOKEN_NAME)
        self.redirect(url)
