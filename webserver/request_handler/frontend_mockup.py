"""
This file is just temporary for testing and evaluation while Angular app is developed
"""
from typing import List

import tornado.web

from application import User
from user_serializer import UserSerializer
from .base import (
    AUTH_TOKEN_NAME,
    SESSION_TOKEN_NAME,
    AuthenticatedUserBase,
    authenticated
)


class FirstPageFrontend(AuthenticatedUserBase):

    def initialize(self, user_serializer: UserSerializer):
        self._user_serializer = user_serializer

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._user_serializer.unserialize(client_cookie)

    def get(self):
        self.render("index.html")


class UnixAccountAuthorizationRequestsFrontend(AuthenticatedUserBase):

    def initialize(self, user_serializer: UserSerializer):
        self._user_serializer = user_serializer

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._user_serializer.unserialize(client_cookie)

    @authenticated
    def get(self):
        self.render("auth-requests.html")


class OpenIDLoginFrontend(AuthenticatedUserBase):

    def initialize(self, user_serializer: UserSerializer, openid_providers_url: List):
        self._user_serializer = user_serializer
        self._openid_providers_url = openid_providers_url

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._user_serializer.unserialize(client_cookie)

    def get(self):
        self.render("login.html", openid_providers_url=self._openid_providers_url)


class UserAccountLogoutFrontend(tornado.web.RequestHandler):

    """ https://www.keycloak.org/docs/latest/securing_apps/index.html#logout-endpoint-2 """

    def initialize(self, callback_url: str):
        self._callback_url = callback_url

    def get(self):
        self.clear_cookie(AUTH_TOKEN_NAME)
        self.clear_cookie(SESSION_TOKEN_NAME)
        self.redirect(self._callback_url)
