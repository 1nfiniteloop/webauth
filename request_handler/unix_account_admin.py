from .base import (
    AuthenticatedUserBase,
    administrator
)
from application import (
    UnixAccount,
    User,
    UserSerializer
)
from formatting import JsonFormattedUnixAccount
from storage import (
    UnixAccountStorage
)


class Parameter(object):
    """ Valid parameters in http requests """
    UNIX_ACCOUNT_NAME, UNIX_ACCOUNT_ID, ASSOCIATED_USER_ID = ("unix_account_name", "unix_account_id", "unix_account_id")


class UnixAccountAdministrationArguments:

    def __init__(self, user_serializer: UserSerializer, storage: UnixAccountStorage):
        self._storage = storage
        self._user_serializer = user_serializer

    @property
    def storage(self) -> UnixAccountStorage:
        return self._storage

    @property
    def user_serializer(self) -> UserSerializer:
        return self._user_serializer


class UnixAccountAdministration(AuthenticatedUserBase):

    def initialize(self, args: UnixAccountAdministrationArguments):
        self._args = args

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._args.user_serializer.unserialize(client_cookie)

    @administrator
    def post(self):
        """ Register a new unix_account """
        unix_accountname = self.get_argument(Parameter.UNIX_ACCOUNT_NAME)
        unix_account_id = self.get_argument(Parameter.UNIX_ACCOUNT_ID)
        associated_user_id = self.get_argument(Parameter.ASSOCIATED_USER_ID, None)
        unix_account_added = self._args.storage.add_unix_account(
            UnixAccount(unix_account_id, unix_accountname),
            associated_user_id
        )
        if not unix_account_added:
            self.set_status(400)

    @administrator
    def delete(self):
        """ Unregister an existing unix_account """
        unix_account_id = self.get_argument(Parameter.UNIX_ACCOUNT_ID)
        unix_account_deleted = self._args.storage.remove_unix_account_by_id(unix_account_id)
        if not unix_account_deleted:
            self.set_status(400)

    @administrator
    def get(self):
        if Parameter.UNIX_ACCOUNT_ID in self.request.arguments:
            unix_account_id = self.get_argument(Parameter.UNIX_ACCOUNT_ID)
            unix_account = self._args.storage.get_unix_account_by_id(unix_account_id)
            unix_accounts = list()
            if unix_account.id:  # database could return "NonexistingUnixAccount"
                unix_accounts.append(JsonFormattedUnixAccount(unix_account))
        else:
            unix_accounts = list(JsonFormattedUnixAccount(unix_account) for unix_account in self._args.storage.get_all_unix_accounts())
        self.write({
            "unix_accounts": unix_accounts
        })


class UnixAccountAssociationAdministration(AuthenticatedUserBase):

    def initialize(self, args: UnixAccountAdministrationArguments):
        self._args = args

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._args.user_serializer.unserialize(client_cookie)

    @administrator
    def post(self, unix_account_id: str):
        user_id = self.get_argument(Parameter.ASSOCIATED_USER_ID)
        if not unix_account_id.isnumeric():
            self.set_status(400, reason="User id must be numeric")
        elif not self._args.storage.associate_user_to_unix_account(user_id, int(unix_account_id)):
            self.set_status(400, reason="Unix account id does not exist")
        else:
            self.set_status(200)

    @administrator
    def delete(self, unix_account_id: str):
        user_id = self.get_argument(Parameter.ASSOCIATED_USER_ID)
        if not unix_account_id.isnumeric():
            self.set_status(400, reason="User id must be numeric")
        elif not self._args.storage.disassociate_user_from_unix_account(user_id, int(unix_account_id)):
            self.set_status(400, reason="Unix account id does not exist")
        else:
            self.set_status(200)

    @administrator
    def get(self, unix_account_id: str):
        if not unix_account_id.isnumeric():
            self.set_status(400, reason="User id must be numeric")
        else:
            associated_users = self._args.storage.get_associated_users_for_unix_account(int(unix_account_id))
            self.write({
                "associated_users": associated_users
            })

