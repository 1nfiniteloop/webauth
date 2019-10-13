import json
import logging
from typing import (
    List,
    Dict
)

from application import (
    Host,
    UnixAccount,
    User
)
from application.storage import (
    HostStorage,
    UnixAccountStorage,
    UserAccountStorage,
    Storage
)
from config import BootstrapConfiguration
from storage import ApplicationUserData


log = logging.getLogger(__name__)


class ConfigurationType:
    USER = "user"
    HOST = "host"
    UNIX_ACCOUNT = "unix_account"


class Attribute:
    """ Attribute in configuration file """
    TYPE = "type"
    NAME = "name"
    ID = "id"
    PRIVILEGE = "privilege"
    ASSOCIATED_USER = "associated_user"


class UserAccountsBootstrap:

    def __init__(self, storage: UserAccountStorage, configurations: List[Dict], users_added: list):
        self._storage = storage
        self._configurations = configurations
        self._users_added = users_added

    def create_from_config(self):
        for cfg in self._configurations:
            self._create(cfg)

    def _create(self, config: dict):
        try:
            self._try_create(config)
        except (KeyError, StopIteration):
            log.error("Invalid formatted configuration for '{type}': {cfg}".format(
                type=ConfigurationType.USER,
                cfg=json.dumps(config)
            ))

    def _try_create(self, config: dict):
        name = config[Attribute.NAME]
        privilege = config[Attribute.PRIVILEGE]
        existing_user = self._storage.get_user_by_name(name)    # NOTE: names are non-unique in the storage
        if not existing_user.id:
            user = self._storage.add_user(ApplicationUserData(
                name,
                self._privilege_from_str(privilege)
            ))
            self._users_added.append(user)
            log.debug("Added '{type}': {name}".format(type=ConfigurationType.USER, name=name))

    def _privilege_from_str(self, privilege_name: str) -> User.Privilege:
        privilege_numeric = next(privilege.value for privilege in User.Privilege if privilege.name == privilege_name)
        return User.Privilege(privilege_numeric)


class HostsBootstrap:

    def __init__(self, storage: HostStorage, configurations: List[Dict]):
        self._storage = storage
        self._configurations = configurations

    def create_from_config(self):
        for cfg in self._configurations:
            self._create(cfg)

    def _create(self, config: dict):
        try:
            self._try_create(config)
        except KeyError:
            log.error("Invalid formatted configuration for '{type}': {cfg}".format(
                type=ConfigurationType.HOST,
                cfg=json.dumps(config)
            ))

    def _try_create(self, config: dict):
        name = config[Attribute.NAME]
        id_ = config[Attribute.ID]
        if not self._storage.host_exists(id_):
            self._storage.add_host(Host(
                id_,
                name
            ))
            log.debug("Added '{type}': {name}".format(type=ConfigurationType.HOST, name=name))


class UnixAccountsBootstrap:

    def __init__(self, storage: UnixAccountStorage, configurations: List[Dict], users_added: list):
        self._storage = storage
        self._configurations = configurations
        self._users_added = users_added

    def create_from_config(self):
        for cfg in self._configurations:
            self._create(cfg)

    def _create(self, config: dict):
        try:
            self._try_create(config)
        except KeyError:
            log.error("Invalid formatted configuration for '{type}': {cfg}".format(
                type=ConfigurationType.UNIX_ACCOUNT,
                cfg=json.dumps(config))
            )

    def _try_create(self, config: dict):
        name = config[Attribute.NAME]
        id_ = config[Attribute.ID]
        if not self._storage.unix_account_exists(id_):
            unix_account = UnixAccount(id_, name)
            if Attribute.ASSOCIATED_USER in config:
                self._storage.add_unix_account(
                    unix_account,
                    self._get_associated_user_id(config[Attribute.ASSOCIATED_USER])
                )
            else:
                self._storage.add_unix_account(unix_account)
            log.debug("Added '{type}': {name}".format(type=ConfigurationType.UNIX_ACCOUNT, name=name))

    def _get_associated_user_id(self, name: str):
        default_value = None
        try:
            return next((user.id for user in self._users_added if user.name == name))
        except StopIteration:
            log.error("Invalid formatted '{attr}': '{name}' does not exist in configuration".format(attr=Attribute.ASSOCIATED_USER, name=name))
            return default_value


def bootstrap_storage(storage: Storage, bootstrap_cfg: BootstrapConfiguration) -> List[User]:
    """ Entrypoint for bootstrapping the application """
    users_added = list()  # order matters, since class "UsersBootstrap" adds users into the list.
    users_bs = UserAccountsBootstrap(storage.user_accounts, bootstrap_cfg.type(ConfigurationType.USER), users_added)
    users_bs.create_from_config()
    hosts_bs = HostsBootstrap(storage.hosts, bootstrap_cfg.type(ConfigurationType.HOST))
    hosts_bs.create_from_config()
    unix_accounts_bs = UnixAccountsBootstrap(storage.unix_accounts, bootstrap_cfg.type(ConfigurationType.UNIX_ACCOUNT), users_added)
    unix_accounts_bs.create_from_config()
    return users_added
