from .configuration import OpenIDEndpoints
from .endpoints import OpenIDEndpointsBuilder


class KeycloakOpenIDEndpoints(OpenIDEndpoints):

    """ Reads the configuration from .well-known  """

    def __init__(self, config: dict):
        self._config = config

    @property
    def issuer(self) -> str:
        return self._config["issuer"]

    @property
    def authorization_endpoint(self) -> str:
        return self._config["authorization_endpoint"]

    @property
    def token_endpoint(self) -> str:
        return self._config["token_endpoint"]

    @property
    def logout_endpoint(self) -> str:
        return self._config["end_session_endpoint"]  # or logout_endpoint for google!!?!

    @property
    def jwks_endpoint(self) -> str:
        return self._config["jwks_uri"]


class KeycloakOpenIDEndpointsBuilder(OpenIDEndpointsBuilder):

    def new(self, well_known: dict) -> OpenIDEndpoints:
        return KeycloakOpenIDEndpoints(well_known)
