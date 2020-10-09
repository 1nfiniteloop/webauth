import tornado.routing

from application.storage import Storage
from application.messaging import MessageBus
from unix_account_authorization import (
    UnixAccountAuthorizationRequest,
    DefaultAuthorizationRequestBuilder
)
from request_handler import (
    UnixAccountAuthorization,
)


def create_route(url: str, msg_bus: MessageBus, storage: Storage) -> tornado.routing.Rule:
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
