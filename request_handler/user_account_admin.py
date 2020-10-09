from .base import (
    AuthenticatedUserBase,
    administrator
)
from application import (
    User,
    UserSerializer
)
from application.storage import (
    UserAccountStorage,
)
from user_account_activation import UserAccountActivationWithLink
from storage import (
    ApplicationUserData,
)
from formatting import (
    JsonFormattedUser
)


class Parameter(object):
    """ Valid parameters in http requests """
    USERNAME, USER_ID, USER_PRIVILEGE = ("username", "unix_account_id", "privilege")


class UserAccountAdministrationArguments:

    def __init__(self, user_serializer: UserSerializer, storage: UserAccountStorage, account_activation: UserAccountActivationWithLink):
        self._storage = storage
        self._user_serializer = user_serializer
        self._account_activation = account_activation

    @property
    def storage(self) -> UserAccountStorage:
        return self._storage

    @property
    def user_serializer(self) -> UserSerializer:
        return self._user_serializer

    @property
    def account_activation(self) -> UserAccountActivationWithLink:
        return self._account_activation


class UserAccountAdministration(AuthenticatedUserBase):

    def initialize(self, args: UserAccountAdministrationArguments):
        self._args = args

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._args.user_serializer.unserialize(client_cookie)

    @administrator
    def post(self):
        """ Register a new user """
        username = self.get_argument(Parameter.USERNAME)
        privilege = self.get_argument(Parameter.USER_PRIVILEGE, default=User.Privilege.USER.value)
        user = self._args.storage.add_user(ApplicationUserData(username, privilege))
        link = self._args.account_activation.activate_account_and_get_link(user)
        response = {
            "activation_link": link
        }
        self.write(response)

    @administrator
    def delete(self):
        """ Unregister an existing user """
        user_id = self.get_argument(Parameter.USER_ID)
        user_deleted = self._args.storage.remove_user_by_id(user_id)
        if not user_deleted:
            self.set_status(400, reason="Failed to delete user")

    @administrator
    def get(self):
        if Parameter.USER_ID in self.request.arguments:
            user_id = self.get_argument(Parameter.USER_ID)
            user = self._args.storage.get_user_by_id(user_id)
            users = list()
            if user.id:  # database could return "NonexistingUser"
                users.append(JsonFormattedUser(user))
        else:
            users = list(JsonFormattedUser(user) for user in self._args.storage.get_all_users())
        self.write({
            "users": users
        })
