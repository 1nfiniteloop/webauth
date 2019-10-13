from .hosts import HostStorage
from .user_accounts import (
    UserAccountStorage,
    UserAccountActivationStorage
)
from .unix_accounts import UnixAccountStorage


class Storage:

    def __init__(self, hosts: HostStorage, user_accounts: UserAccountStorage, unix_accounts: UnixAccountStorage, user_account_activations: UserAccountActivationStorage):
        self._hosts = hosts
        self._user_accounts = user_accounts
        self._user_account_activations = user_account_activations
        self._unix_accounts = unix_accounts

    @property
    def user_accounts(self) -> UserAccountStorage:
        return self._user_accounts

    @property
    def user_account_activations(self) -> UserAccountActivationStorage:
        return self._user_account_activations

    @property
    def hosts(self) -> HostStorage:
        return self._hosts

    @property
    def unix_accounts(self) -> UnixAccountStorage:
        return self._unix_accounts
