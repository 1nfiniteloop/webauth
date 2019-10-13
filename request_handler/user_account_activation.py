from application import (
    User
)
from application.storage import UserAccountActivationStorage
from user_serializer import (
    UserSerializer,
)

from .base import (
    AUTH_TOKEN_NAME,
    AuthenticatedUserBase
)


class UserAccountActivationArguments:

    def __init__(self, user_serializer: UserSerializer, storage: UserAccountActivationStorage):
        self._user_serializer = user_serializer
        self._storage = storage

    @property
    def storage(self) -> UserAccountActivationStorage:
        return self._storage

    @property
    def user_serializer(self) -> UserSerializer:
        return self._user_serializer


class UserAccountActivation(AuthenticatedUserBase):

    def initialize(self, args: UserAccountActivationArguments):
        self._args = args

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._args.user_serializer.unserialize(client_cookie)

    def set_authenticated_user(self, user: User):
        self.set_secure_cookie(AUTH_TOKEN_NAME, self.serialize_user(user))

    def serialize_user(self, user: User) -> str:
        return self._args.user_serializer.serialize(user)

    def get(self, nonce: str):
        next = self.get_argument("next")
        user = self._args.storage.pop_user(nonce)
        if user.id:
            self.set_authenticated_user(user)
            self.redirect(next)
        else:
            self.set_status(400)
