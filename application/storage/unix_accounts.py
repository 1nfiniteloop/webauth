from abc import (
    ABC,
    abstractmethod
)

from ..unix_account import UnixAccount


class NonExistingUnixAccount(UnixAccount):
    """ Represents a non-existing unix_account returned when no record found in database, identified by an empty id """
    def __init__(self):
        super().__init__(id_=0, name="nonexisting-account")


class UnixAccountStorage(ABC):

    @abstractmethod
    def add_unix_account(self, unix_account: UnixAccount, associated_user_id: str = None) -> bool:
        """Returns True if added successfully, False if item already exists"""
        pass

    @abstractmethod
    def unix_account_exists(self, id_: int) -> bool:
        pass

    @abstractmethod
    def remove_unix_account_by_id(self, id_: int) -> bool:
        """Returns True if is deleted successfully, False if item don't exists"""
        pass

    @abstractmethod
    def get_unix_account_by_id(self, id_: int) -> UnixAccount:
        pass

    @abstractmethod
    def get_all_unix_accounts(self) -> list:
        pass

    @abstractmethod
    def associate_user_to_unix_account(self, user_id: str, unix_account_id: int) -> bool:
        pass

    @abstractmethod
    def disassociate_user_from_unix_account(self, user_id: str, unix_account_id: int) -> bool:
        pass

    @abstractmethod
    def get_associated_users_for_unix_account(self, unix_account_id: int) -> list:
        pass
