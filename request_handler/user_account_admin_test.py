import unittest
from unittest.mock import Mock
import urllib.parse

import tornado.escape
import tornado.httputil
from tornado.testing import AsyncHTTPTestCase
import tornado.web

from .user_account_admin import (
    UserAccountAdministrationArguments,
    UserAccountAdministration,
    Parameter
)
from application import User
from user_account_activation import UserAccountActivationWithLink
from stubs import (
    UserAccountStorageStub,
    UserSerializerStub,
    UnprivilegedUser
)


admin_user = User(id_="0123-4567", name="admin", privilege=User.Privilege.ADMINISTRATOR)
regular_user = User(id_="1234-5678", name="not-admin", privilege=User.Privilege.USER)
activation_link = "http://localhost/1234-5678"


class TestUserUserAccountAdministration(AsyncHTTPTestCase):
    API_ENDPOINT = "/api/admin/user"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_serializer = UserSerializerStub()
        self._user_storage = UserAccountStorageStub()
        self._user_registration = Mock(spec=UserAccountActivationWithLink)

    def setUp(self):
        super().setUp()
        self._user_serializer.set_response_data_for("unserialize", UnprivilegedUser())
        self._user_storage.reset_stub()
        self._user_registration.reset_mock()
        self._user_registration.activate_account_and_get_link.return_value = activation_link

    def _set_logged_in_user(self, user: User):
        self._user_serializer.set_response_data_for("unserialize", user)

    def get_app(self):
        args = UserAccountAdministrationArguments(
            self._user_serializer,
            self._user_storage,
            self._user_registration
        )
        return tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (self.API_ENDPOINT, UserAccountAdministration, dict(args=args)),
            ])

    def test_register_user_with_empty_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(self.API_ENDPOINT, method="POST", body="")
        self.assertEqual(400, response.code)

    def test_register_user_with_invalid_data(self):
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

    def test_register_user_from_not_logged_in_user(self):
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.USERNAME: "new-user"
            })
        )
        self.assertEqual(401, response.code)

    def test_register_user_from_unprivileged_user(self):
        self._set_logged_in_user(regular_user)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.USERNAME: "new-user"
            })
        )
        self.assertEqual(401, response.code)

    def test_register_valid_user(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.USERNAME: "new-user",
            })
        )
        self.assertEqual(200, response.code)

    def test_get_activation_link_when_register_valid_user(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.USERNAME: "new-user",
            })
        )
        response = tornado.escape.json_decode(response.body)
        self.assertEqual(activation_link, response["activation_link"])

    def test_unregister_user_with_empty_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(self.API_ENDPOINT, method="DELETE")
        self.assertEqual(400, response.code)

    def test_unregister_user_from_not_logged_in_user(self):
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.USER_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(401, response.code)

    def test_unregister_user_from_unprivileged_user(self):
        self._set_logged_in_user(regular_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.USER_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(401, response.code)

    def test_unregister_non_existing_user(self):
        self._user_storage.set_response_data_for("remove_user_by_id", value=False)
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.USER_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(400, response.code)

    def test_unregister_existing_user(self):
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.USER_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(200, response.code)

    def test_get_one_user(self):
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.USER_ID: "1234-5678"
        })
        response = self.fetch(url, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        returned_users = decoded_response["users"]
        self.assertEqual(200, response.code)
        # NOTE: response below assumes that "UserStorageStub" is returning the correct.
        self.assertEqual(len(returned_users), 1, "Expects to return one user")

    def test_get_all_users(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(self.API_ENDPOINT, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        returned_users = decoded_response["users"]
        self.assertEqual(200, response.code)
        # NOTE: response below assumes that "UserStorageStub" is returning the correct.
        self.assertNotEqual(len(returned_users), 0, "Expects to return a non-empty list of all users")

    def test_get_nonexisting_user(self):
        nonexisting_user = User("", "")
        self._user_storage.set_response_data_for("get_user_by_id", value=nonexisting_user)
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.USER_ID: "1234-5678"
        })
        response = self.fetch(url, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        returned_users = decoded_response["users"]
        self.assertEqual(len(returned_users), 0, "Expects to return an empty list of users")


if __name__ == "__main__":
    unittest.main()
