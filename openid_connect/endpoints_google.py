from .configuration import OpenIDEndpoints
from .endpoints import OpenIDEndpointsBuilder


class GoogleOpenIDEndpoints(OpenIDEndpoints):

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
        # NOTE: Endpoint is not present in well-known, using hard-coded endpoint:
        logout_endpoint = "https://accounts.google.com/Logout"
        return logout_endpoint  # self._config["logout_endpoint"]

    @property
    def jwks_endpoint(self) -> str:
        return self._config["jwks_uri"]


class GoogleOpenIDEndpointsBuilder(OpenIDEndpointsBuilder):

    def new(self, well_known: dict) -> OpenIDEndpoints:
        return GoogleOpenIDEndpoints(well_known)
