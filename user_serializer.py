import json

from application import (
    User,
    UserSerializer,
    UnprivilegedUser,
)
from formatting import (
    JsonFormattedUser,
    UserAttribute
)


class AuthenticatedUserSerializer(UserSerializer):

    def serialize(self, user: User) -> str:
        return json.dumps(JsonFormattedUser(user))

    def unserialize(self, user_data: str) -> User:
        if user_data:
            user = self._try_unserialize(user_data)
        else:
            user = UnprivilegedUser()
        return user

    def _try_unserialize(self, user_data: str) -> User:
        try:
            user_data = json.loads(user_data)
            user = self._convert_json_to_user(user_data)
        except json.decoder.JSONDecodeError:
            user = UnprivilegedUser()
        except KeyError:
            user = UnprivilegedUser()
        return user

    def _convert_json_to_user(self, user_data: dict) -> User:
        args = [
            user_data[UserAttribute.USER_ID],
            user_data[UserAttribute.USER_NAME],
            User.Privilege(user_data[UserAttribute.USER_PRIVILEGE])
        ]
        return User(*args)
