import unittest
from unittest.mock import (
    Mock,
    call,
    ANY
)

from application import UnixAccount
from application.storage import (
    NonExistingUnixAccount,
    IOStorage
)
from .unix_accounts import JsonFormattedUnixAccountStorage


valid_unix_account = UnixAccount(id_=1, name="unix-account-name")
valid_user_id = "123-456-789"


class TestJsonFormattedUnixAccountStorage(unittest.TestCase):

    def __init__(self, *args):
        super().__init__(*args)
        self._storage = Mock(spec=IOStorage)

    def setUp(self):
        self._reset_mock()

    def _reset_mock(self):
        self._storage.reset_mock()
        self._storage.read.return_value = "[]"

    def test_load_on_init(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        self._storage.read.assert_called_once()

    def test_load_empty_storage(self):
        self._storage.read.side_effect = FileNotFoundError
        storage = JsonFormattedUnixAccountStorage(self._storage)
        # non-existing file is ok, file will be created on save

    def test_get_nonexisting_unix_account_by_id(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        unix_account = storage.get_unix_account_by_id(id_=0)
        self.assertIs(type(unix_account), NonExistingUnixAccount)

    def test_add_existing_unix_account(self):
        expected_calls = [
            call(ANY),  # add_unix_account
        ]
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(UnixAccount(id_=1, name="another-unix_account"))  # id is the unique constraint
        self.assertFalse(storage.add_unix_account(valid_unix_account))
        self._storage.write.assert_has_calls(expected_calls)

    def test_add_unix_account(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        self.assertTrue(storage.add_unix_account(valid_unix_account))
        self._storage.write.assert_called_once()

    def test_add_unix_account_and_associate_user(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        self.assertTrue(storage.add_unix_account(valid_unix_account, valid_user_id))
        self._storage.write.assert_called_once()

    def test_add_and_get_unix_account(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(valid_unix_account)
        fetched = storage.get_unix_account_by_id(valid_unix_account.id)
        self.assertEqual(
            vars(valid_unix_account),
            vars(fetched)
        )

    def test_remove_unix_account(self):
        expected_calls = [
            call(ANY),  # add_unix_account
            call(ANY),  # remove_unix_account_by_id
        ]
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(valid_unix_account)
        self.assertTrue(storage.remove_unix_account_by_id(id_=1))
        self._storage.write.assert_has_calls(expected_calls)

    def test_remove_nonexisting_unix_account(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        self.assertFalse(storage.remove_unix_account_by_id(id_=1))
        self._storage.write.assert_not_called()

    def test_get_all_unix_accounts(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(valid_unix_account)
        storage.add_unix_account(UnixAccount(id_=2, name="another-unix-account"))
        all_unix_accounts = storage.get_all_unix_accounts()
        self.assertEqual(len(all_unix_accounts), 2)

    def test_associate_user_to_existing_unix_account(self):
        expected_calls = [
            call(ANY),  # add_unix_account
            call(ANY),  # associate_user_to_unix_account
        ]
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(valid_unix_account)
        success = storage.associate_user_to_unix_account(valid_user_id, valid_unix_account.id)
        self.assertTrue(success)
        self._storage.write.assert_has_calls(expected_calls)

    def test_associate_non_unique_user_to_unix_account(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(valid_unix_account, associated_user_id=valid_user_id)
        success = storage.associate_user_to_unix_account(valid_user_id, valid_unix_account.id)
        self.assertFalse(success)

    def test_associate_user_to_non_existing_unix_account(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        success = storage.associate_user_to_unix_account(valid_user_id, 123)
        self.assertFalse(success)
        self._storage.write.assert_not_called()

    def test_disassociate_user_from_unix_account(self):
        expected_calls = [
            call(ANY),  # add_unix_account
            call(ANY),  # disassociate_user_from_unix_account
        ]
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(valid_unix_account, associated_user_id=valid_user_id)
        success = storage.disassociate_user_from_unix_account(valid_user_id, valid_unix_account.id)
        self.assertTrue(success)
        self._storage.write.assert_has_calls(expected_calls)

    def test_disassociate_user_from_non_existing_unix_account(self):
        expected_calls = [
            call(ANY),  # add_unix_account
        ]
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(valid_unix_account, associated_user_id=valid_user_id)
        success = storage.disassociate_user_from_unix_account(valid_user_id, 123)
        self.assertFalse(success)
        self._storage.write.assert_has_calls(expected_calls)

    def test_get_associated_users_from_existing_unix_account(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(valid_unix_account, associated_user_id=valid_user_id)
        user_id_s = storage.get_associated_users_for_unix_account(valid_unix_account.id)
        self.assertEqual(len(user_id_s), 1)
        self.assertEqual(user_id_s[0], valid_user_id)

    def test_get_associated_users_from_non_existing_unix_account(self):
        storage = JsonFormattedUnixAccountStorage(self._storage)
        storage.add_unix_account(valid_unix_account)
        users = storage.get_associated_users_for_unix_account(123)
        self.assertEqual(len(users), 0)
