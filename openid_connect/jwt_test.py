from datetime import timedelta
import unittest
from unittest.mock import Mock

from .jwt import JWKPublicKeyCache

default_key_id = "123"
default_keys = {
    "keys": [
        {"kid": "123"},
        {"kid": "456"},
    ]
}


class TestJWKPublicKeyCache(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._callback = Mock()

    def setUp(self):
        self.reset_mock()

    def reset_mock(self):
        self._callback.reset_mock()
        self._callback.return_value = default_keys

    def test_dont_fetch_keys_on_init(self):
        _ = JWKPublicKeyCache(self._callback)
        self._callback.assert_not_called()

    def test_fetch_keys_on_first_call(self):
        cache = JWKPublicKeyCache(self._callback)
        _ = cache.key(default_key_id)
        self._callback.assert_called_once()

    def test_get_non_existing_key(self):
        cache = JWKPublicKeyCache(self._callback)
        keys = cache.key("234")
        self.assertFalse(keys)

    def test_cache_updated_when_expired(self):
        cache = JWKPublicKeyCache(self._callback, update_interval=timedelta(seconds=0))
        _ = cache.key(default_key_id)
        _ = cache.key(default_key_id)
        _ = cache.key(default_key_id)
        self.assertEqual(3, self._callback.call_count)

    def test_cache_not_updated_when_not_expired(self):
        cache = JWKPublicKeyCache(self._callback, update_interval=timedelta(hours=1))
        _ = cache.key(default_key_id)
        _ = cache.key(default_key_id)
        _ = cache.key(default_key_id)
        self._callback.assert_called_once()
