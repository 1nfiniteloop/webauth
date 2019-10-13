from application.storage import UnixAccountStorage
from application import UnixAccount
from ..response_mixin import StubResponseMixin

unix_account = UnixAccount(1000, "account-name")


class UnixAccountStorageStub(UnixAccountStorage, StubResponseMixin):

    def default_response_data(self) -> dict:
        response_data = {
            "add_unix_account": True,
            "unix_account_exists": False,
            "remove_unix_account_by_id": True,
            "get_unix_account_by_id": unix_account,
            "get_all_unix_accounts": [unix_account],
            "associate_user_to_unix_account": True,
            "disassociate_user_from_unix_account": True,
            "get_associated_users_for_unix_account": ["1234-56778"]
        }
        return response_data

    def add_unix_account(self, unix_account: UnixAccount, associated_user_id: str = None) -> bool:
        """Returns True if added successfully, False if item already exists"""
        return self._response_data["add_unix_account"]

    def unix_account_exists(self, id_: int) -> bool:
        return self.get_response()

    def remove_unix_account_by_id(self, id_: int) -> bool:
        """Returns True if is deleted successfully, False if item don't exists"""
        return self.get_response()

    def get_unix_account_by_id(self, id_: int) -> UnixAccount:
        return self.get_response()

    def get_all_unix_accounts(self) -> list:
        return self.get_response()

    def associate_user_to_unix_account(self, user_id: str, unix_account_id: int) -> bool:
        return self.get_response()

    def disassociate_user_from_unix_account(self, user_id: str, unix_account_id: int) -> bool:
        return self.get_response()

    def get_associated_users_for_unix_account(self, unix_account_id: int) -> list:
        return self.get_response()
