from typing import Dict
import json

from application.endpoints import (
    OpenIDProviderEndpoint,
    UserEndpoints,
    UserEndpointsSerializer
)


class JsonFormattedUserEndpoints(dict):

    def __init__(self, endpoints: UserEndpoints):
        formatted = {
            "api_endpoints": endpoints.api_endpoints,
            "user_registration": endpoints.user_registration,
            "websocket": endpoints.websocket_url,
            "logout": endpoints.logout,
            "identity_provider": self._serialize_openid_providers(endpoints.openid_providers)
        }
        super().__init__(formatted)

    def _serialize_openid_providers(self, openid_providers: Dict[str, OpenIDProviderEndpoint]) -> list:
        formatted = []
        for name, provider in openid_providers.items():
            formatted.append(JsonFormattedOpenIDProviderEndpoint(provider))
        return formatted


class JsonFormattedOpenIDProviderEndpoint(dict):

    def __init__(self, endpoint: OpenIDProviderEndpoint):
        formatted = {
            "name": endpoint.name,
            "login": endpoint.login,
            "logout": endpoint.logout,
            "register": endpoint.register
        }
        super().__init__(formatted)


class JsonUserEndpointsSerializer(UserEndpointsSerializer):

    def serialize(self, endpoints: UserEndpoints) -> str:
        return json.dumps(JsonFormattedUserEndpoints(endpoints))
