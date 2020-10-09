from typing import List
import tornado.routing

from application.messaging import MessageBus
from application.storage import UserAccountActivationStorage
from endpoints_serializer import (
    JsonUserEndpointsSerializer,
    UserEndpoints,
)
from request_handler import (
    ApiEndpoints,
    ApiEndpointsArguments,
    UserAccountLogout,
    UnixAccountAuthorizationWebsocketArguments,
    UnixAccountAuthorizationWebsocket,
    UserAccountActivation,
    UserAccountActivationArguments,
)
from unix_account_authorization import (
    MessageProtocol,
)
from user_serializer import AuthenticatedUserSerializer
from utils import url_path_join


def create_routes(endpoints: UserEndpoints, msg_bus: MessageBus, protocol: MessageProtocol, new_user_accounts: UserAccountActivationStorage) -> List[tornado.routing.Rule]:
    routes = [
        tornado.routing.Rule(
            tornado.routing.PathMatches(endpoints.api_endpoints),
            ApiEndpoints,
            dict(args=ApiEndpointsArguments(endpoints, JsonUserEndpointsSerializer()))),
        tornado.routing.Rule(
            tornado.routing.PathMatches(endpoints.websocket),
            UnixAccountAuthorizationWebsocket,
            dict(args=UnixAccountAuthorizationWebsocketArguments(msg_bus, AuthenticatedUserSerializer(), protocol))),
        tornado.routing.Rule(
            tornado.routing.PathMatches(url_path_join(endpoints.user_registration, "(.*)")),
            UserAccountActivation,
            dict(args=UserAccountActivationArguments(AuthenticatedUserSerializer(), new_user_accounts))),
        tornado.routing.Rule(
            tornado.routing.PathMatches(endpoints.logout),
            UserAccountLogout)
    ]
    return routes
