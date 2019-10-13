from typing import List

import tornado.routing

from application.storage import Storage
from request_handler import (
    HostAdministrationArguments,
    HostAdministration,
    UnixAccountAdministrationArguments,
    UnixAccountAdministration,
    UserAccountAdministrationArguments,
    UserAccountAdministration,
)
from user_account_activation import UserAccountActivationWithLink
from user_serializer import AuthenticatedUserSerializer


class RoutesUrl:

    def __init__(self, host_admin: str, unix_account_admin: str, user_account_admin: str):
        self._host_admin = host_admin
        self._unix_account_admin = unix_account_admin
        self._user_account_admin = user_account_admin

    @property
    def host_admin(self) -> str:
        return self._host_admin

    @property
    def unix_account_admin(self) -> str:
        return self._unix_account_admin

    @property
    def user_account_admin(self):
        return self._user_account_admin


def create_routes(url: RoutesUrl, storage: Storage, user_account_activation: UserAccountActivationWithLink) -> List[tornado.routing.Rule]:
    user_serializer = AuthenticatedUserSerializer()
    routes = [
        tornado.routing.Rule(
            tornado.routing.PathMatches(url.host_admin),
            HostAdministration,
            dict(args=HostAdministrationArguments(user_serializer, storage.hosts))
        ),
        tornado.routing.Rule(
            tornado.routing.PathMatches(url.unix_account_admin),
            UnixAccountAdministration,
            dict(args=UnixAccountAdministrationArguments(user_serializer, storage.unix_accounts))
        ),
        tornado.routing.Rule(
            tornado.routing.PathMatches(url.user_account_admin),
            UserAccountAdministration,
            dict(args=UserAccountAdministrationArguments(user_serializer, storage.user_accounts, user_account_activation))
        )
    ]
    return routes
