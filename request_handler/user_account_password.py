import tornado.web

from application import (
    User,
    UserSerializer,
    UserAccountAuthentication
)
from user_account_password import PasswordCredentials

from .base import (
    AUTH_TOKEN_NAME,
    AuthenticatedUserBase,
)


class Parameter(object):
    USERNAME, PASSWORD = "username", "password"


class UserAccountPasswordLogin(AuthenticatedUserBase):

    def initialize(self, user_serializer: UserSerializer, user_auth: UserAccountAuthentication, app_base_url: str):
        self._user_serializer = user_serializer
        self._user_auth = user_auth
        self._app_base_url = app_base_url

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._user_serializer.unserialize(client_cookie)

    def serialize_user(self, user: User) -> str:
        return self._user_serializer.serialize(user)

    def _authenticate(self, username: str, password: str):
        user = self._user_auth.authenticate(PasswordCredentials(username, password))
        if user.privilege.value:  # != User.Privilege.NONE:
            self.set_secure_cookie(AUTH_TOKEN_NAME, self.serialize_user(user))
            authenticated = True
        else:
            authenticated = False
        return authenticated

    def post(self):
        username = self.get_argument(Parameter.USERNAME)
        password = self.get_argument(Parameter.PASSWORD)
        if self.current_user.id:
            self.redirect(self.get_argument("next", self._app_base_url))
        elif self._authenticate(username, password):
            self.redirect(self.get_argument("next", self._app_base_url))
        else:
            raise tornado.web.HTTPError(401)


class UserAccountPasswordLogout(tornado.web.RequestHandler):

    def initialize(self, app_base_url: str):
        self._app_base_url = app_base_url

    def get(self):
        self.clear_cookie(AUTH_TOKEN_NAME)
        self.redirect(self.get_argument("next", self._app_base_url))
