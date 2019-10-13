import unittest
from unittest.mock import (
    Mock,
    call,
    ANY
)
from application import User
from application.storage import (
    HostStorage,
    UnixAccountStorage,
    UserAccountStorage,
    NonExistingUser
)
from bootstrap_storage import (
    Attribute,
    HostsBootstrap,
    UnixAccountsBootstrap,
    UserAccountsBootstrap
)


class TestUserAccountsBootstrap(unittest.TestCase):

    def test_init_with_non_valid_config(self):
        config = [{"asd": 123}]
        init = UserAccountsBootstrap(Mock(spec=UserAccountStorage), config, list())
        init.create_from_config()

    def test_bad_formatted_privilege(self):
        storage = Mock(spec=UserAccountStorage)
        storage.get_user_by_name.return_value = NonExistingUser()
        config = [{
            Attribute.TYPE: "user",
            Attribute.NAME: "username",
            Attribute.PRIVILEGE: "NONEXISTING_PRIVILEGE"
        }]
        init = UserAccountsBootstrap(storage, config, list())
        init.create_from_config()
        storage.add_user.assert_not_called()

    def test_create_user_with_valid_config(self):
        storage = Mock(spec=UserAccountStorage)
        storage.get_user_by_name.return_value = NonExistingUser()
        config = [{
            Attribute.TYPE: "user",
            Attribute.NAME: "username",
            Attribute.PRIVILEGE: "USER"
        }]
        init = UserAccountsBootstrap(storage, config, list())
        init.create_from_config()
        storage.add_user.assert_called_once()

    def test_add_created_users_in_list(self):
        added_users = list()
        storage = Mock(spec=UserAccountStorage)
        storage.get_user_by_name.return_value = NonExistingUser()
        config = [{
            Attribute.TYPE: "user",
            Attribute.NAME: "username",
            Attribute.PRIVILEGE: "USER"
        }]
        init = UserAccountsBootstrap(storage, config, added_users)
        init.create_from_config()
        self.assertEqual(len(added_users), 1)

    def test_create_user_when_already_exists(self):
        storage = Mock(spec=UserAccountStorage)
        storage.get_user_by_name.return_value = User("1234-5678", "username")
        config = [{
            Attribute.TYPE: "user",
            Attribute.NAME: "username",
            Attribute.PRIVILEGE: "USER"
        }]
        init = UserAccountsBootstrap(storage, config, list())
        init.create_from_config()
        storage.add_user.assert_not_called()


class TestHostsBootstrap(unittest.TestCase):

    def test_init_with_non_valid_config(self):
        config = [{"asd": 123}]
        init = HostsBootstrap(Mock(spec=HostStorage), config)
        init.create_from_config()

    def test_create_host_with_valid_config(self):
        storage = Mock(spec=HostStorage)
        storage.host_exists.return_value = False
        config = [{
            Attribute.TYPE: "host",
            Attribute.NAME: "hostname",
            Attribute.ID: "1234-5678"
        }]
        init = HostsBootstrap(storage, config)
        init.create_from_config()
        storage.add_host.assert_called_once()

    def test_create_host_when_already_exists(self):
        storage = Mock(spec=HostStorage)
        storage.host_exists.return_value = True
        config = [{
            Attribute.TYPE: "host",
            Attribute.NAME: "hostname",
            Attribute.ID: "1234-5678"
        }]
        init = HostsBootstrap(storage, config)
        init.create_from_config()
        storage.add_host.assert_not_called()


class TestUnixAccountsBootstrap(unittest.TestCase):

    def test_init_with_non_valid_config(self):
        added_users = list()
        config = [{"asd": 123}]
        init = UnixAccountsBootstrap(Mock(spec=UnixAccountStorage), config, added_users)
        init.create_from_config()

    def test_create_unix_account_with_valid_config(self):
        added_users = list()
        storage = Mock(spec=UnixAccountStorage)
        storage.unix_account_exists.return_value = False
        config = [{
            Attribute.TYPE: "unix_account",
            Attribute.NAME: "unix_account_name",
            Attribute.ID: 1001
        }]
        init = UnixAccountsBootstrap(storage, config, added_users)
        init.create_from_config()
        storage.add_unix_account.assert_called_once()

    def test_create_unix_account_with_associated_user(self):
        user_id, username = "1234-5678", "user-name"
        added_users = [User(user_id, username)]
        storage = Mock(spec=UnixAccountStorage)
        storage.unix_account_exists.return_value = False
        config = [{
            Attribute.TYPE: "unix_account",
            Attribute.NAME: "unix_account_name",
            Attribute.ID: 1001,
            Attribute.ASSOCIATED_USER: username,
        }]
        init = UnixAccountsBootstrap(storage, config, added_users)
        init.create_from_config()
        expected_calls = [
            call(ANY, user_id)
        ]
        storage.add_unix_account.assert_has_calls(expected_calls)

    def test_create_unix_account_with_non_existing_associated_user(self):
        user_id, username = "1234-5678", "user-name"
        added_users = [User(user_id, username)]
        storage = Mock(spec=UnixAccountStorage)
        storage.unix_account_exists.return_value = False
        config = [{
            Attribute.TYPE: "unix_account",
            Attribute.NAME: "unix_account_name",
            Attribute.ID: 1001,
            Attribute.ASSOCIATED_USER: "nonexisting-username",
        }]
        init = UnixAccountsBootstrap(storage, config, added_users)
        init.create_from_config()
        expected_calls = [
            call(ANY, None)
        ]
        storage.add_unix_account.assert_has_calls(expected_calls)

    def test_create_unix_account_when_already_exists(self):
        added_users = list()
        storage = Mock(spec=UnixAccountStorage)
        storage.unix_account_exists.return_value = True
        config = [{
            Attribute.TYPE: "unix_account",
            Attribute.NAME: "unix_account_name",
            Attribute.ID: 1001
        }]
        init = UnixAccountsBootstrap(storage, config, added_users)
        init.create_from_config()
        storage.add_unix_account.assert_not_called()
