import unittest
import urllib.parse

import tornado.escape
import tornado.httputil
from tornado.testing import AsyncHTTPTestCase
import tornado.web

from application import (
    Host,
    User
)
from .host_admin import (
    HostAdministration,
    HostAdministrationArguments,
    Parameter
)
from stubs import (
    UserSerializerStub,
    HostStorageStub,
    UnprivilegedUser
)

admin_user = User(id_="0123-4567", name="admin", privilege=User.Privilege.ADMINISTRATOR)
regular_user = User(id_="1234-5678", name="not-admin", privilege=User.Privilege.USER)


class TestHostAdministration(AsyncHTTPTestCase):
    API_ENDPOINT = "/api/admin/host"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_serializer = UserSerializerStub()
        self._host_storage = HostStorageStub()

    def setUp(self):
        super().setUp()
        self._user_serializer.set_response_data_for("unserialize", UnprivilegedUser())
        self._host_storage.reset_stub()

    def _set_logged_in_user(self, user: User):
        self._user_serializer.set_response_data_for("unserialize", user)

    def get_app(self):
        args = HostAdministrationArguments(
            self._user_serializer,
            self._host_storage,
        )
        return tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (self.API_ENDPOINT, HostAdministration, dict(args=args)),
            ])

    def test_register_host_with_empty_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(self.API_ENDPOINT, method="POST", body="")
        self.assertEqual(400, response.code)

    def test_register_host_with_invalid_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                "asd": "123",
                "message": "hello-world"
            })
        )
        self.assertEqual(400, response.code)

    def test_register_host_from_not_logged_in_user(self):
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.HOSTNAME: "new-host"
            })
        )
        self.assertEqual(401, response.code)

    def test_register_host_from_unprivileged_user(self):
        self._set_logged_in_user(regular_user)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.HOSTNAME: "new-host"
            })
        )
        self.assertEqual(401, response.code)

    def test_register_valid_host(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.HOSTNAME: "new-host",
                Parameter.HOST_ID: "123-456-789"
            })
        )
        self.assertEqual(200, response.code)

    def test_register_already_existing_host(self):
        self._set_logged_in_user(admin_user)
        self._host_storage.set_response_data_for("add_host", value=False)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.HOSTNAME: "new-host",
                Parameter.HOST_ID: "123-456-789"
            })
        )
        self.assertEqual(400, response.code)

    def test_unregister_host_with_empty_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(self.API_ENDPOINT, method="DELETE")
        self.assertEqual(400, response.code)

    def test_unregister_host_from_not_logged_in_user(self):
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.HOST_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(401, response.code)

    def test_unregister_host_from_unprivileged_user(self):
        self._set_logged_in_user(regular_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.HOST_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(401, response.code)

    def test_unregister_non_existing_host(self):
        self._host_storage.set_response_data_for("remove_host_by_id", value=False)
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.HOST_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(400, response.code)

    def test_unregister_existing_host(self):
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.HOST_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(200, response.code)

    def test_get_one_host(self):
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.HOST_ID: "1234-5678"
        })
        response = self.fetch(url, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        self.assertEqual(200, response.code)
        self.assertIn("hosts", decoded_response)
        # NOTE: response below assumes that "HostStorageStub" is returning correct.
        self.assertEqual(len(decoded_response["hosts"]), 1, "Expects to return one host")

    def test_get_all_hosts(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(self.API_ENDPOINT, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        self.assertEqual(200, response.code)
        self.assertIn("hosts", decoded_response)
        # NOTE: response below assumes that "HostStorageStub" is returning correct.
        self.assertNotEqual(len(decoded_response["hosts"]), 0, "Expects to return a non-empty list of all hosts")

    def test_get_nonexisting_host(self):
        nonexisting_host = Host("", "")
        self._set_logged_in_user(admin_user)
        self._host_storage.set_response_data_for("get_host_by_id", value=nonexisting_host)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.HOST_ID: "1234-5678"
        })
        response = self.fetch(url, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        self.assertIn("hosts", decoded_response)
        self.assertEqual(len(decoded_response["hosts"]), 0, "Expects to return an empty list of all hosts")


if __name__ == "__main__":
    unittest.main()
