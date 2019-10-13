import unittest
from unittest.mock import (
    Mock,
    call,
    ANY
)
from application import Host
from application.storage import (
    NonExistingHost,
    IOStorage
)
from .hosts import JsonFormattedHostStorage

valid_host = Host(id_="1234-5678", name="hostname")


class TestJsonFormattedHostStorage(unittest.TestCase):

    def __init__(self, *args):
        super().__init__(*args)
        self._storage = Mock(spec=IOStorage)

    def setUp(self):
        self._reset_mock()

    def _reset_mock(self):
        self._storage.reset_mock()
        self._storage.read.return_value = "[]"

    def test_load_on_init(self):
        storage = JsonFormattedHostStorage(self._storage)
        self._storage.read.assert_called_once()

    def test_load_empty_storage(self):
        self._storage.read.side_effect = FileNotFoundError
        storage = JsonFormattedHostStorage(self._storage)
        # non-existing file is ok, file will be created on save

    def test_get_nonexisting_host_by_id(self):
        storage = JsonFormattedHostStorage(self._storage)
        host = storage.get_host_by_id(id_="1234-5678")
        self.assertIs(type(host), NonExistingHost)

    def test_add_existing_host(self):
        storage = JsonFormattedHostStorage(self._storage)
        storage.add_host(Host(id_="1234-5678", name="another-host"))  # id is the unique constraint
        self.assertFalse(storage.add_host(valid_host))
        self._storage.write.assert_called_once()

    def test_add_host(self):
        storage = JsonFormattedHostStorage(self._storage)
        self.assertTrue(storage.add_host(valid_host))
        self._storage.write.assert_called_once()

    def test_add_and_get_host(self):
        storage = JsonFormattedHostStorage(self._storage)
        storage.add_host(valid_host)
        fetched = storage.get_host_by_id(valid_host.id)
        self.assertEqual(
            vars(valid_host),
            vars(fetched)
        )

    def test_remove_host(self):
        expected_calls = [
            call(ANY),  # add_host
            call(ANY)   # remove_host
        ]
        storage = JsonFormattedHostStorage(self._storage)
        storage.add_host(valid_host)
        self.assertTrue(storage.remove_host_by_id(id_="1234-5678"))
        self._storage.write.assert_has_calls(expected_calls)

    def test_remove_nonexisting_host(self):
        storage = JsonFormattedHostStorage(self._storage)
        self.assertFalse(storage.remove_host_by_id(id_="1234-5678"))
        self._storage.write.assert_not_called()

    def test_get_all_hosts(self):
        storage = JsonFormattedHostStorage(self._storage)
        storage.add_host(valid_host)
        storage.add_host(Host(id_="2345-6789", name="another-host"))
        all_hosts = storage.get_all_hosts()
        self.assertEqual(len(all_hosts), 2)
