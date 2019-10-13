from abc import (
    ABC,
    abstractmethod
)
from typing import (
    Dict,
    List
)

from ..user import User


class NonExistingUser(User):
    """ Represents a non-existing user returned when no record found in database, identified by an empty id """
    def __init__(self):
        super().__init__(id_="", name="nonexisting-user", privilege=User.Privilege.NONE)


# Type aliases
UserIdentity = Dict[str, str]
UserData = Dict


class UserAccountStorage(ABC):

    @abstractmethod
    def add_user(self, user: UserData, identity: UserIdentity = None) -> User:
        """  Add user with optionally extern identnty (OpenID), returns a user """
        pass

    @abstractmethod
    def user_exist(self, id_: str) -> bool:
        pass

    @abstractmethod
    def remove_user_by_id(self, id_: str) -> bool:
        """Returns True if user is deleted successfully, False if user don't exists"""
        pass

    @abstractmethod
    def get_user_by_id(self, id_: str) -> User:
        pass

    @abstractmethod
    def get_user_by_name(self, name: str) -> User:
        pass

    @abstractmethod
    def get_all_users(self) -> List[User]:
        pass

    @abstractmethod
    def add_identity_to_user(self, id_: str, identity: UserIdentity) -> bool:
        """ Returns true if user exists and identity don't already exist """
        pass

    @abstractmethod
    def get_user_by_identity(self, identity: UserIdentity) -> User:
        pass


class UserAccountActivationStorage(ABC):

    @abstractmethod
    def put_user(self, user: User) -> str:
        pass

    @abstractmethod
    def pop_user(self, nonce: str) -> User:
        pass
