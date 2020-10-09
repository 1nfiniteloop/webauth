from typing import List

import tornado.routing

from application.storage import Storage
from user_account_activation import (
    UserAccountActivationWithLink,
    UserAccountActivationLinkBuilder
)
from formatting import AuthenticatedUserSerializer

from request_handler import (
    HostAdministrationArguments,
    HostAdministration,
    UnixAccountAdministrationArguments,
    UnixAccountAdministration,
    UserAccountAdministrationArguments,
    UserAccountAdministration,
)
from config import AdministrationEndpoints


def create_routes(endpoint: AdministrationEndpoints, storage: Storage, link_builder: UserAccountActivationLinkBuilder) -> List[tornado.routing.Rule]:
    account_link_activation = UserAccountActivationWithLink(
        storage.user_account_activations,
        link_builder
    )
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
            dict(args=UserAccountAdministrationArguments(user_serializer, storage.user_accounts, account_link_activation)))
    ]
    return routes
