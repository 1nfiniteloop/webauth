from typing import List

import tornado.routing

from application.storage import Storage
from user_account_activation import UserAccountActivationWithLink
from user_serializer import AuthenticatedUserSerializer

from request_handler import (
    HostAdministrationArguments,
    HostAdministration,
    UnixAccountAdministrationArguments,
    UnixAccountAdministration,
    UserAccountAdministrationArguments,
    UserAccountAdministration,
)
from config import AdministrationEndpoints


def create_routes(endpoint: AdministrationEndpoints, storage: Storage, user_account_activation: UserAccountActivationWithLink) -> List[tornado.routing.Rule]:
    user_serializer = AuthenticatedUserSerializer()
    routes = [
        tornado.routing.Rule(
            tornado.routing.PathMatches(endpoint.hosts),
            HostAdministration,
            dict(args=HostAdministrationArguments(user_serializer, storage.hosts))),
        tornado.routing.Rule(
            tornado.routing.PathMatches(endpoint.unix_accounts),
            UnixAccountAdministration,
            dict(args=UnixAccountAdministrationArguments(user_serializer, storage.unix_accounts))),
        tornado.routing.Rule(
            tornado.routing.PathMatches(endpoint.user_accounts),
            UserAccountAdministration,
            dict(args=UserAccountAdministrationArguments(user_serializer, storage.user_accounts, user_account_activation)))
    ]
    return routes
