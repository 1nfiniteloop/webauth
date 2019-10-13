from abc import (
    ABC,
    abstractproperty
)


class OpenIDEndpoints(ABC):

    @abstractproperty
    def issuer(self) -> str:
        pass

    @abstractproperty
    def authorization_endpoint(self) -> str:
        pass

    @abstractproperty
    def token_endpoint(self) -> str:
        pass

    @abstractproperty
    def logout_endpoint(self) -> str:
        pass

    @abstractproperty
    def jwks_endpoint(self) -> str:
        pass


class OpenIDEndpointsBuilder(ABC):

    def new(self, well_known: dict) -> OpenIDEndpoints:
        pass
