from application import (
    UserSerializer,
    UnprivilegedUser
)
from application import User
from ..response_mixin import StubResponseMixin


class UserSerializerStub(UserSerializer, StubResponseMixin):

    """ stub for when a request handler calls 'get_current_user()' or 'current_user' """

    def default_response_data(self) -> dict:
        response_data = {
            "unserialize": UnprivilegedUser(),
            "serialize": "some cookie content"
        }
        return response_data

    def unserialize(self, raw: str) -> User:
        """ Implements method in interface """
        return self.get_response()

    def serialize(self, user: User) -> str:
        """ Implements method in interface """
        return self.get_response()
