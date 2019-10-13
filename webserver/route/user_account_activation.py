import tornado.routing

from application.storage import UserAccountActivationStorage
from request_handler import (
    UserAccountActivation,
    UserAccountActivationArguments
)
from user_serializer import AuthenticatedUserSerializer

from ..utils import url_path_join


def create_route(new_user_accounts: UserAccountActivationStorage, url_base_path: str) -> tornado.routing.Rule:
    args = UserAccountActivationArguments(
        AuthenticatedUserSerializer(),
        new_user_accounts
    )
    rule = tornado.routing.Rule(
        tornado.routing.PathMatches(url_path_join(url_base_path, "(.*)")),
        UserAccountActivation,
        dict(args=args)
    )
    return rule
