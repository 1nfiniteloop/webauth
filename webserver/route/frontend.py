import tornado.routing
from ..request_handler import Frontend


def create_route(path: str) -> tornado.routing.Rule:
    return tornado.routing.Rule(
        tornado.routing.PathMatches(path),
        Frontend)
