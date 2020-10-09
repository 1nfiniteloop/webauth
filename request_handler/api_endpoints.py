import tornado.web

from application import (
    UserEndpoints,
    UserEndpointsSerializer
)
import base64


CONFIGURATION = "api_endpoints"


class ApiEndpointsArguments:

    def __init__(self, endpoints: UserEndpoints, serializer: UserEndpointsSerializer):
        self._endpoints = endpoints
        self._serializer = serializer

    @property
    def endpoints(self) -> UserEndpoints:
        return self._endpoints

    @property
    def serializer(self) -> UserEndpointsSerializer:
        return self._serializer


class ApiEndpoints(tornado.web.RequestHandler):

    def initialize(self, args: ApiEndpointsArguments):
        self._args = args

    def _serialize_configuration(self) -> bytes:
        return base64.b64encode(bytes(self._args.serializer.serialize(self._args.endpoints), encoding="utf8"))

    def get(self):
        next = self.get_argument("next", "/")
        self.set_cookie(CONFIGURATION, self._serialize_configuration())
        self.redirect(next)
