from typing import List
import tornado.routing

from application.messaging import MessageBus
from application.storage import UserAccountActivationStorage
from application import (
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
    WebsocketMessageProtocol
)
from formatting import (
    AuthenticatedUserSerializer,
    JsonUserEndpointsSerializer
)
from utils import url_path_join


def create_routes(endpoints: UserEndpoints, msg_bus: MessageBus, new_user_accounts: UserAccountActivationStorage) -> List[tornado.routing.Rule]:
    routes = [
        tornado.routing.Rule(
            tornado.routing.PathMatches(endpoints.api_endpoints),
            ApiEndpoints,
            dict(args=ApiEndpointsArguments(endpoints, JsonUserEndpointsSerializer()))),
        tornado.routing.Rule(
            tornado.routing.PathMatches(endpoints.websocket),
            UnixAccountAuthorizationWebsocket,
            dict(args=UnixAccountAuthorizationWebsocketArguments(msg_bus, AuthenticatedUserSerializer(), WebsocketMessageProtocol()))),
        tornado.routing.Rule(
            tornado.routing.PathMatches(url_path_join(endpoints.user_registration, "(.*)")),
            UserAccountActivation,
            dict(args=UserAccountActivationArguments(AuthenticatedUserSerializer(), new_user_accounts))),
        tornado.routing.Rule(
            tornado.routing.PathMatches(endpoints.logout),
            UserAccountLogout)
    ]
    return routes
