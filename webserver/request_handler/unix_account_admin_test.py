import unittest
import urllib.parse

import tornado.escape
import tornado.httputil
from tornado.testing import AsyncHTTPTestCase
import tornado.web

from application import (
    UnixAccount,
    User
)
from .unix_account_admin import (
    UnixAccountAdministration,
    UnixAccountAdministrationArguments,
    UnixAccountAssociationAdministration,
    Parameter
)
from stubs import (
    UserSerializerStub,
    UnixAccountStorageStub,
    UnprivilegedUser
)

admin_user = User(id_="0123-4567", name="admin", privilege=User.Privilege.ADMINISTRATOR)
regular_user = User(id_="1234-5678", name="not-admin", privilege=User.Privilege.USER)

# default parameters used in test cases below
user_id = "1234-5678"
unix_account_id = "1000"


class TestUnixAccountAdministration(AsyncHTTPTestCase):
    API_ENDPOINT = "/api/admin/unix-account"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_serializer = UserSerializerStub()
        self._storage = UnixAccountStorageStub()

    def setUp(self):
        super().setUp()
        self._user_serializer.set_response_data_for("unserialize", UnprivilegedUser())
        self._storage.reset_stub()

    def _set_logged_in_user(self, user: User):
        self._user_serializer.set_response_data_for("unserialize", user)

    def get_app(self):
        args = UnixAccountAdministrationArguments(
            self._user_serializer,
            self._storage,
        )
        return tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (self.API_ENDPOINT, UnixAccountAdministration, dict(args=args)),
            ])

    def test_register_unix_account_with_empty_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(self.API_ENDPOINT, method="POST", body="")
        self.assertEqual(400, response.code)

    def test_register_unix_account_with_invalid_data(self):
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

    def test_register_unix_account_from_not_logged_in_user(self):
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_NAME: "new-unix-account"
            })
        )
        self.assertEqual(401, response.code)

    def test_register_unix_account_from_unprivileged_user(self):
        self._set_logged_in_user(regular_user)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_NAME: "new-unix-account"
            })
        )
        self.assertEqual(401, response.code)

    def test_register_valid_unix_account(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_NAME: "new-unix-account",
                Parameter.UNIX_ACCOUNT_ID: "123-456-789"
            })
        )
        self.assertEqual(200, response.code)

    def test_register_already_existing_unix_account(self):
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("add_unix_account", value=False)
        response = self.fetch(
            self.API_ENDPOINT,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.UNIX_ACCOUNT_NAME: "new-unix-account",
                Parameter.UNIX_ACCOUNT_ID: "123-456-789"
            })
        )
        self.assertEqual(400, response.code)

    # --------- test unregister/delete unix accounts ---------

    def test_unregister_unix_account_with_empty_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(self.API_ENDPOINT, method="DELETE")
        self.assertEqual(400, response.code)

    def test_unregister_unix_account_from_not_logged_in_user(self):
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.UNIX_ACCOUNT_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(401, response.code)

    def test_unregister_unix_account_from_unprivileged_user(self):
        self._set_logged_in_user(regular_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.UNIX_ACCOUNT_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(401, response.code)

    def test_unregister_non_existing_unix_account(self):
        self._storage.set_response_data_for("remove_unix_account_by_id", value=False)
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.UNIX_ACCOUNT_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(400, response.code)

    def test_unregister_existing_unix_account(self):
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.UNIX_ACCOUNT_ID: "1234-5678"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(200, response.code)

    # --------- test get unix accounts ---------

    def test_get_one_unix_account(self):
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.UNIX_ACCOUNT_ID: "1234-5678"
        })
        response = self.fetch(url, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        self.assertEqual(200, response.code)
        self.assertIn("unix_accounts", decoded_response)

    def test_get_all_unix_accounts(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(self.API_ENDPOINT, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        returned_unix_accounts = decoded_response["unix_accounts"]
        self.assertEqual(200, response.code)
        # NOTE: response below assumes that "UnixAccountStorageStub" is behaving correct.
        self.assertNotEqual(len(returned_unix_accounts), 0, "Expects to return a non-empty list of all unix_accounts")

    def test_get_nonexisting_unix_account(self):
        nonexisting_unix_account = UnixAccount(0, "")
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("get_unix_account_by_id", value=nonexisting_unix_account)
        url = tornado.httputil.url_concat(self.API_ENDPOINT, {
            Parameter.UNIX_ACCOUNT_ID: "1234-5678"
        })
        response = self.fetch(url, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        returned_unix_accounts = decoded_response["unix_accounts"]
        # NOTE: response below assumes that "UnixAccountStorageStub" is behaving correct.
        self.assertEqual(len(returned_unix_accounts), 0, "Expects to return an empty list of unix_account")


class TestUnixAccountAssociationAdministration(AsyncHTTPTestCase):
    API_ENDPOINT = "/api/admin/unix-account"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_serializer = UserSerializerStub()
        self._storage = UnixAccountStorageStub()

    def setUp(self):
        super().setUp()
        self._user_serializer.set_response_data_for("unserialize", UnprivilegedUser())
        self._storage.reset_stub()

    def _set_logged_in_user(self, user: User):
        self._user_serializer.set_response_data_for("unserialize", user)

    def get_app(self):
        args = UnixAccountAdministrationArguments(
            self._user_serializer,
            self._storage,
        )
        return tornado.web.Application(
            cookie_secret="secret",
            handlers=[
                (self.API_ENDPOINT + "/(.+)", UnixAccountAssociationAdministration, dict(args=args)),
            ])

    # --------- test associate ---------

    def test_associate_user_to_unix_account_with_empty_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(
            self.API_ENDPOINT + "/" + unix_account_id,
            method="POST",
            body=""
        )
        self.assertEqual(400, response.code)

    def test_associate_unix_account_with_invalid_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(
            self.API_ENDPOINT + "/" + unix_account_id,
            method="POST",
            body=urllib.parse.urlencode({
                "asd": "123",
                "message": "hello-world"
            })
        )
        self.assertEqual(400, response.code)

    def test_associate_user_to_unix_account_from_not_logged_in_user(self):
        response = self.fetch(
            self.API_ENDPOINT + "/" + unix_account_id,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.ASSOCIATED_USER_ID: user_id
            })
        )
        self.assertEqual(401, response.code)

    def test_associate_user_to_unix_account_from_unprivileged_user(self):
        self._set_logged_in_user(regular_user)
        response = self.fetch(
            self.API_ENDPOINT + "/" + unix_account_id,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.ASSOCIATED_USER_ID: user_id
            })
        )
        self.assertEqual(401, response.code)

    def test_associate_user_to_valid_unix_account(self):
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("associate_user_to_unix_account", value=True)
        response = self.fetch(
            self.API_ENDPOINT + "/" + unix_account_id,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.ASSOCIATED_USER_ID: user_id
            })
        )
        self.assertEqual(200, response.code)

    def test_associate_user_to_non_valid_unix_account(self):
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("associate_user_to_unix_account", value=False)
        response = self.fetch(
            self.API_ENDPOINT + "/" + unix_account_id,
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.ASSOCIATED_USER_ID: user_id
            })
        )
        self.assertEqual(400, response.code)

    def test_associate_user_on_non_numeric_unix_account_id(self):
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("associate_user_to_unix_account", value=True)
        response = self.fetch(
            self.API_ENDPOINT + "/" + "non-numeric-id",
            method="POST",
            body=urllib.parse.urlencode({
                Parameter.ASSOCIATED_USER_ID: user_id
            })
        )
        self.assertEqual(400, response.code)

    # --------- test disassociate ---------

    def test_disassociate_user_to_unix_account_with_empty_data(self):
        self._set_logged_in_user(admin_user)
        response = self.fetch(
            self.API_ENDPOINT + "/" + unix_account_id,
            method="DELETE"
        )
        self.assertEqual(400, response.code)

    def test_disassociate_unix_account_with_invalid_data(self):
        self._set_logged_in_user(admin_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT + "/" + unix_account_id, {
            "asd": "123",
            "message": "hello-world"
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(400, response.code)

    def test_disassociate_user_to_unix_account_from_not_logged_in_user(self):
        url = tornado.httputil.url_concat(self.API_ENDPOINT + "/" + unix_account_id, {
            Parameter.ASSOCIATED_USER_ID: user_id
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(401, response.code)

    def test_disassociate_user_to_unix_account_from_unprivileged_user(self):
        self._set_logged_in_user(regular_user)
        url = tornado.httputil.url_concat(self.API_ENDPOINT + "/" + unix_account_id, {
            Parameter.ASSOCIATED_USER_ID: user_id
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(401, response.code)

    def test_disassociate_user_from_valid_unix_account(self):
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("disassociate_user_from_unix_account", value=True)
        url = tornado.httputil.url_concat(self.API_ENDPOINT + "/" + unix_account_id, {
            Parameter.ASSOCIATED_USER_ID: user_id
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(200, response.code)

    def test_disassociate_user_from_non_valid_unix_account(self):
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("disassociate_user_from_unix_account", value=False)
        url = tornado.httputil.url_concat(self.API_ENDPOINT + "/" + unix_account_id, {
            Parameter.ASSOCIATED_USER_ID: user_id
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(400, response.code)

    def test_disassociate_user_on_non_numeric_unix_account_id(self):
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("disassociate_user_from_unix_account", value=True)
        url = tornado.httputil.url_concat(self.API_ENDPOINT + "/" + "non-numeric-id", {
            Parameter.ASSOCIATED_USER_ID: user_id
        })
        response = self.fetch(url, method="DELETE")
        self.assertEqual(400, response.code)

    # --------- test get associations ---------

    def test_get_associated_users_to_unix_account_from_not_logged_in_user(self):
        url = self.API_ENDPOINT + "/" + unix_account_id
        response = self.fetch(url, method="GET")
        self.assertEqual(401, response.code)

    def test_get_associated_users_to_unix_account_from_unprivileged_user(self):
        self._set_logged_in_user(regular_user)
        url = self.API_ENDPOINT + "/" + unix_account_id
        response = self.fetch(url, method="GET")
        self.assertEqual(401, response.code)

    def test_get_associated_users_from_valid_unix_account(self):
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("get_associated_users_for_unix_account", value=["1234", "2345", "3456"])
        url = self.API_ENDPOINT + "/" + unix_account_id
        response = self.fetch(url, method="GET")
        decoded_response = tornado.escape.json_decode(response.body)
        self.assertEqual(200, response.code)
        self.assertIn("associated_users", decoded_response)

    def test_get_associated_users_on_non_numeric_unix_account_id(self):
        self._set_logged_in_user(admin_user)
        self._storage.set_response_data_for("get_associated_users_for_unix_account", value=["1234", "2345", "3456"])
        url = self.API_ENDPOINT + "/" + "non-numeric-id"
        response = self.fetch(url, method="GET")
        self.assertEqual(400, response.code)


if __name__ == "__main__":
    unittest.main()
