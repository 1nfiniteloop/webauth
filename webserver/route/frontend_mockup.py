from typing import (
    List,
    Dict
)

import tornado.routing

from request_handler import (
    FirstPageFrontend,
    OpenIDLoginFrontend,
    UnixAccountAuthorizationRequestsFrontend,
    UserAccountLogoutFrontend
)
from user_serializer import AuthenticatedUserSerializer


class RoutesUrl:

    def __init__(self, main_path: str, login_path: str, logout_path: str, authorization_requests_path: str):
        self._main_path = main_path
        self._login_path = login_path
        self._logout_path = logout_path
        self._authorization_requests_path = authorization_requests_path

    @property
    def main(self) -> str:
        return self._main_path

    @property
    def login(self) -> str:
        return self._login_path

    @property
    def logout(self) -> str:
        return self._logout_path

    @property
    def authorization_requests(self) -> str:
        return self._authorization_requests_path


def create_routes(url: RoutesUrl, openid_providers: Dict) -> List[tornado.routing.Rule]:
    user_serializer = AuthenticatedUserSerializer()
    routes = [
        tornado.routing.Rule(
            tornado.routing.PathMatches(url.main),
            FirstPageFrontend,
            dict(user_serializer=user_serializer)
        ),
        tornado.routing.Rule(
            tornado.routing.PathMatches(url.login),
            OpenIDLoginFrontend,
            dict(user_serializer=user_serializer, openid_providers_url=openid_providers)
        ),
        tornado.routing.Rule(
            tornado.routing.PathMatches(url.authorization_requests),
            UnixAccountAuthorizationRequestsFrontend,
            dict(user_serializer=user_serializer)
        ),
        tornado.routing.Rule(
            tornado.routing.PathMatches(url.logout),
            UserAccountLogoutFrontend,
            dict(callback_url=url.main)
        )
    ]
    return routes
