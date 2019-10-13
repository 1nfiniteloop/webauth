import unittest
from unittest.mock import (
    Mock,
    call,
    ANY
)

from application import User
from application.storage import (
    IOStorage,
    NonExistingUser,
    UserIdentity
)
from .user_accounts import (
    JsonFormattedUserAccountStorage,
    UserAccountActivationInMemoryStorage,
    ApplicationUserData,
    UniqueConstraintFailed,
)

class OpenIdIdentityStub(UserIdentity):

    def __init__(self, issuer: str, client_id: str, user_id: str):
        item = {
            "type": "openid",
            "issuer": issuer,
            "client_id": client_id,
            "unix_account_id": user_id
        }
        super().__init__(item)


valid_user_data = ApplicationUserData(name="username", privilege=User.Privilege.ADMINISTRATOR)
another_valid_user_data = ApplicationUserData(name="another-user", privilege=User.Privilege.USER)
valid_identity = OpenIdIdentityStub(issuer="example.com", client_id="my-app", user_id="12345")


class TestJsonFormattedUserStorage(unittest.TestCase):

    def __init__(self, *args):
        super().__init__(*args)
        self._storage = Mock(spec=IOStorage)

    def setUp(self):
        self._reset_mock()

    def _reset_mock(self):
        self._storage.reset_mock()
        self._storage.read.return_value = "[]"

    def test_load_on_init(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        self._storage.read.assert_called_once()

    def test_load_empty_storage(self):
        self._storage.read.side_effect = FileNotFoundError
        storage = JsonFormattedUserAccountStorage(self._storage)
        # non-existing file is ok, file will be created on save

    def test_get_nonexisting_user_by_id(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.get_user_by_id(id_="asdf")
        self.assertIs(type(user), NonExistingUser)

    def test_get_nonexisting_user_by_name(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.get_user_by_name(name="username")
        self.assertIs(type(user), NonExistingUser)

    def test_add_user(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data)
        self.assertEqual(user.name, valid_user_data["name"])
        self.assertEqual(user.privilege, valid_user_data["privilege"])
        self._storage.write.assert_called_once()

    def test_add_user_and_identity(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data, valid_identity)
        self.assertEqual(user.name, valid_user_data["name"])
        self.assertEqual(user.privilege, valid_user_data["privilege"])

    def test_add_user_and_non_unique_identity(self):
        expected_calls = [
            call(ANY),  # add_user (only once, first time)
        ]
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data, valid_identity)
        with self.assertRaises(UniqueConstraintFailed):
            another_user = storage.add_user(another_valid_user_data, valid_identity)
        self._storage.write.assert_has_calls(expected_calls)

    def test_add_and_get_user(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data)
        returned_user = storage.get_user_by_id(user.id)
        self.assertDictEqual(
            vars(user),
            vars(returned_user)
        )

    def test_remove_user(self):
        expected_calls = [
            call(ANY),  # add_user
            call(ANY),  # remove_user_by_id
        ]
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data)
        self.assertTrue(storage.remove_user_by_id(id_=user.id))
        self._storage.write.assert_has_calls(expected_calls)

    def test_remove_nonexisting_user(self):
        expected_calls = [
            call(ANY),  # add_user
        ]
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data)
        self.assertFalse(storage.remove_user_by_id(id_="asdf"))
        self._storage.write.assert_has_calls(expected_calls)

    def test_add_unique_identity_to_existing_user(self):
        expected_calls = [
            call(ANY),  # add_user
            call(ANY),  # add_identity_to_user
        ]
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data)
        self.assertTrue(storage.add_identity_to_user(user.id, valid_identity))
        self._storage.write.assert_has_calls(expected_calls)

    def test_add_non_unique_identity_to_existing_user(self):
        expected_calls = [
            call(ANY),  # add_user
            call(ANY),  # add_user
        ]
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data, valid_identity)
        another_user = storage.add_user(another_valid_user_data)
        self.assertFalse(storage.add_identity_to_user(another_user.id, valid_identity))
        self._storage.write.assert_has_calls(expected_calls)

    def test_add_identity_to_non_existing_user(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        self.assertFalse(storage.add_identity_to_user("123", valid_identity))
        self._storage.write.assert_not_called()

    def test_get_user_by_existing_identity(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data, valid_identity)
        storage.add_identity_to_user(user.id, OpenIdIdentityStub(issuer="another-example.com", client_id="my-app", user_id="12345"))
        returned_user = storage.get_user_by_identity(valid_identity)
        self.assertDictEqual(
            vars(user),
            vars(returned_user)
        )

    def test_get_user_by_non_existing_identity(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        user = storage.add_user(valid_user_data)
        returned_user = storage.get_user_by_identity(valid_identity)
        self.assertIs(type(returned_user), NonExistingUser)

    def test_get_all_users(self):
        storage = JsonFormattedUserAccountStorage(self._storage)
        storage.add_user(valid_user_data)
        storage.add_user(another_valid_user_data)
        all_users = storage.get_all_users()
        self.assertEqual(len(all_users), 2)


class TestUserAccountActivationInMemoryStorage(unittest.TestCase):

    def test_put_user(self):
        new_accounts = UserAccountActivationInMemoryStorage()
        nonce = new_accounts.put_user(User("user-id", "username"))
        self.assertIsNotNone(nonce)

    def test_pop_user(self):
        user = User("user-id", "username")
        new_accounts = UserAccountActivationInMemoryStorage()
        nonce = new_accounts.put_user(user)
        received_user = new_accounts.pop_user(nonce)
        self.assertIs(user, received_user)

    def test_nonce(self):
        """ It shall be possible to receive user only once """
        user = User("user-id", "username")
        new_accounts = UserAccountActivationInMemoryStorage()
        nonce = new_accounts.put_user(user)
        new_accounts.pop_user(nonce)
        received_user = new_accounts.pop_user(nonce)
        self.assertFalse(received_user.id)

    def test_pop_nonexisting_user(self):
        new_accounts = UserAccountActivationInMemoryStorage()
        received_user = new_accounts.pop_user("12345678")
        self.assertFalse(received_user.id)
