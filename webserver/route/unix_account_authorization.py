import tornado.routing

from application.storage import Storage
from application.messaging import MessageBus
from unix_account_authorization import (
    MessageProtocol,
    UnixAccountAuthorizationRequest,
    DefaultAuthorizationRequestBuilder
)
from user_serializer import AuthenticatedUserSerializer

from ..request_handler import (
    UnixAccountAuthorizationWebsocketArguments,
    UnixAccountAuthorizationWebsocket,
    UnixAccountAuthorization,
)


def create_route_websocket(url: str, msg_bus: MessageBus, protocol: MessageProtocol) -> tornado.routing.Rule:
    user_serializer = AuthenticatedUserSerializer()
    route = tornado.routing.Rule(
        tornado.routing.PathMatches(url),
        UnixAccountAuthorizationWebsocket,
        dict(args=UnixAccountAuthorizationWebsocketArguments(msg_bus, user_serializer, protocol))
    )
    return route


def create_route_backchannel(url: str, msg_bus: MessageBus, storage: Storage) -> tornado.routing.Rule:
    authorization = UnixAccountAuthorizationRequest(
        msg_bus,
        storage.unix_accounts,
        storage.hosts,
        DefaultAuthorizationRequestBuilder()
    )
    route = tornado.routing.Rule(
        tornado.routing.PathMatches(url),
        UnixAccountAuthorization,
        dict(auth=authorization)
    )
    return route
