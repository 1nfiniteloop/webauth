import unittest
import json
from application import (
    User,
    UnprivilegedUser
)
from .user import (
    AuthenticatedUserSerializer,
    UserAttribute,
)


class TestUserAuthTokenConverter(unittest.TestCase):

    def test_serialize_user(self):
        user_data = [
            123,
            "username",
            User.Privilege.ADMINISTRATOR  # = 1
        ]
        user = User(*user_data)
        expected = json.dumps(dict(
            id=user.id,
            name=user.name,
            privilege=user.privilege.value)
        )
        conv = AuthenticatedUserSerializer()
        self.assertEqual(expected, conv.serialize(user))

    def test_unserialize_user_with_empty_data(self):
        """When cookie is not set we expect to return an unprivileged user  """
        conv = AuthenticatedUserSerializer()
        user = conv.unserialize(None)
        expected = UnprivilegedUser()
        self.assertEqual(expected.id, user.id)
        self.assertEqual(expected.name, user.name)
        self.assertEqual(expected.privilege, user.privilege)

    def test_unserialize_user_with_bad_data(self):
        """When cookie is not set we expect to return an unprivileged user  """
        conv = AuthenticatedUserSerializer()
        user = conv.unserialize("crap-data")
        expected = UnprivilegedUser()
        self.assertEqual(expected.id, user.id)
        self.assertEqual(expected.name, user.name)
        self.assertEqual(expected.privilege, user.privilege)

    def test_unserialize_user_with_bad_formatting(self):
        """When cookie is not set we expect to return an unprivileged user  """
        conv = AuthenticatedUserSerializer()
        bad_data = json.dumps(dict(
            asd=123)
        )
        user = conv.unserialize(bad_data)
        expected = UnprivilegedUser()
        self.assertEqual(expected.id, user.id)
        self.assertEqual(expected.name, user.name)
        self.assertEqual(expected.privilege, user.privilege)

    def test_gunserialize_user(self):
        raw_json = {
            UserAttribute.USER_ID: 123,
            UserAttribute.USER_NAME: "username",
            UserAttribute.USER_PRIVILEGE: 1  # = User.Privilege.ADMINISTRATOR
        }
        conv = AuthenticatedUserSerializer()
        user = conv.unserialize(json.dumps(raw_json))
        self.assertEqual(raw_json[UserAttribute.USER_ID], user.id)
        self.assertEqual(raw_json[UserAttribute.USER_NAME], user.name)
        self.assertEqual(
            User.Privilege(raw_json[UserAttribute.USER_PRIVILEGE]),
            user.privilege
        )


if __name__ == "__main__":
    unittest.main()
