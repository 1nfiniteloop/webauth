import json

from application import UnixAccount
from application.storage import (
    IOStorage,
    UnixAccountStorage,
    NonExistingUnixAccount
)

class JsonAttribute:
    """  String literals for all json attributes (don't repeat yourself) """
    name, id, associations = "name", "id", "associated_user_accounts"


class JsonFormattedUnixAccountStorage(UnixAccountStorage):

    def __init__(self, storage: IOStorage):
        self._storage = storage
        self._accounts = self._load()

    def _load(self) -> list:
        try:
            data = self._storage.read()
            hosts = json.loads(data)
        except FileNotFoundError:
            hosts = list()
        return hosts

    def _save(self):
        data = json.dumps(self._accounts, indent=4)
        self._storage.write(data)

    def add_unix_account(self, unix_account: UnixAccount, associated_user_id: str = None) -> bool:
        """Returns True if added successfully, False if item already exists"""
        if self.unix_account_exists(unix_account.id):
            unix_account_added = False
        else:
            associations = list()
            if associated_user_id:
                associations.append(associated_user_id)
            json_formatted_unix_account = {
                JsonAttribute.name: unix_account.name,
                JsonAttribute.id: unix_account.id,
                JsonAttribute.associations: associations
            }
            self._accounts.append(json_formatted_unix_account)
            self._save()
            unix_account_added = True
        return unix_account_added

    def unix_account_exists(self, id_: int) -> bool:
        matches = filter(lambda unix_account: unix_account[JsonAttribute.id] == id_, self._accounts)
        return any(matches)

    def remove_unix_account_by_id(self, id_: int) -> bool:
        """Returns True if is deleted successfully, False if item don't exists"""
        unix_account = self._get_unix_account_by_id(id_)
        if unix_account:
            self._accounts.remove(unix_account)
            self._save()
            unix_account_removed = True
        else:
            unix_account_removed = False
        return unix_account_removed

    def get_unix_account_by_id(self, id_: int) -> UnixAccount:
        unix_account = self._get_unix_account_by_id(id_)
        if unix_account:
            return self._unserialize_unix_account(unix_account)
        else:
            return NonExistingUnixAccount()

    def _get_unix_account_by_id(self, id_: int) -> dict:
        default_value = dict()
        return next((unix_account for unix_account in self._accounts if unix_account[JsonAttribute.id] == id_), default_value)

    def get_all_unix_accounts(self) -> list:
        unix_accounts = list(self._unserialize_unix_account(unix_account) for unix_account in self._accounts)
        return unix_accounts

    def _unserialize_unix_account(self, json_formatted_unix_account: dict) -> UnixAccount:
        unix_account = UnixAccount(
            json_formatted_unix_account[JsonAttribute.id],
            json_formatted_unix_account[JsonAttribute.name]
        )
        return unix_account

    def associate_user_to_unix_account(self, user_id: str, unix_account_id: int) -> bool:
        unix_account = self._get_unix_account_by_id(unix_account_id)
        if unix_account and self._is_user_id_unique(unix_account, user_id):
            associations = unix_account[JsonAttribute.associations]
            associations.append(user_id)
            self._save()
            association_added = True
        else:
            association_added = False
        return association_added

    def _is_user_id_unique(self, unix_account: dict, user_id: str) -> bool:
        matches_found = any((user_id == existing_user_id for existing_user_id in unix_account[JsonAttribute.associations]))
        return not matches_found

    def disassociate_user_from_unix_account(self, user_id: str, unix_account_id: int) -> bool:
        unix_account = self._get_unix_account_by_id(unix_account_id)
        if unix_account:
            associations = unix_account[JsonAttribute.associations]
            associations.remove(user_id)
            self._save()
            association_removed = True
        else:
            association_removed = False
        return association_removed

    def get_associated_users_for_unix_account(self, id_: int) -> list:
        default_return_value = list()
        unix_account = self._get_unix_account_by_id(id_)
        return unix_account.get(JsonAttribute.associations, default_return_value)

    def __str__(self) -> str:
        return json.dumps(self._accounts, indent=4)
