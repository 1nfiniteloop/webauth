from abc import (
    ABC,
    abstractmethod
)
from typing import Dict

from .user import User


# type aliases
Credentials = Dict


class UnprivilegedUser(User):

    """ Represents an unprivileged not logged in user """

    def __init__(self):
        super().__init__("", "unprivileged", User.Privilege.NONE)


class UserAccountAuthentication(ABC):

    @abstractmethod
    def authenticate(self, credentials: Credentials) -> User:
        pass


class UserAccountRegistration(ABC):

    @abstractmethod
    def register_user(self, credentials: Credentials) -> User:
        pass

    @abstractmethod
    def register_identity(self, existing_user: User, credentials: Credentials) -> bool:
        pass
