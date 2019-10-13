import json
import uuid

from application import User
from application.storage import (
    IOStorage,
    UserAccountStorage,
    UserAccountActivationStorage,
    UserIdentity,
    UserData,
    NonExistingUser
)

class JsonAttribute:
    """  String literals for all json attributes (don't repeat yourself) """
    name, id, privilege, user, identities, credentials = "name", "id", "privilege", "user", "identities", "credentials"


class ApplicationUserData(UserData):
    """ Parameters required for storing a User """
    def __init__(self, name: str, privilege: User.Privilege = User.Privilege.USER):
        userdata = {
            JsonAttribute.name: name,
            JsonAttribute.privilege: privilege
        }
        super().__init__(userdata)


class UniqueConstraintFailed(Exception):
    """ Exception raised if unique constraint failed """
    pass



class UserIdentityMapping:

    def __init__(self, user: dict, identity: dict):
        self._user = user
        self._identity = identity

    @property
    def user(self) -> dict:
        return self._user

    @property
    def identity(self) -> dict:
        return self._identity


class UserIdentityMappingIterator:

    """ Helper class for iterating over user and its identities """
    def __init__(self, users: list):
        self._users = users

    def __iter__(self):
        return self._iter()

    def _iter(self):
        for user_record in self._users:
            yield from self._yield_identity_map(user_record)

    def _yield_identity_map(self, user_record):
        for identity in user_record[JsonAttribute.identities]:
            yield UserIdentityMapping(user_record[JsonAttribute.user], identity)


class JsonFormattedUserAccountStorage(UserAccountStorage):

    class JsonFormattedUser(dict):
        """ Represents a json formatted user in the database """
        def __init__(self, user: User):
            user = {
                JsonAttribute.name: user.name,
                JsonAttribute.id: user.id,
                JsonAttribute.privilege: user.privilege.value
            }
            super().__init__(user)

    def __init__(self, storage: IOStorage):
        self._storage = storage
        self._users = self._load()

    def _load(self) -> list:
        try:
            data = self._storage.read()
            hosts = json.loads(data)
        except FileNotFoundError:
            hosts = list()
        return hosts

    def _save(self):
        data = json.dumps(self._users, indent=4)
        self._storage.write(data)

    def add_user(self, user_data: ApplicationUserData, identity: UserIdentity = None) -> User:
        user_id = uuid.uuid4()
        user = User(
            str(user_id),
            user_data[JsonAttribute.name],
            user_data[JsonAttribute.privilege]
        )
        user_record = self._new_user(user, identity)
        self._users.append(user_record)
        self._save()
        return user

    def _new_user(self, user: User, identity: UserIdentity = None) -> dict:
        identities = list()
        credentials = list()  # not implemented but reserved for credentials: password, PublicKey, ...
        user_record = {
            JsonAttribute.user: self.JsonFormattedUser(user),
            JsonAttribute.identities: identities,
            JsonAttribute.credentials: credentials
        }
        if identity:
            self._try_add_identity(identities, identity)
        return user_record

    def _try_add_identity(self, user_identities: list, identity: UserIdentity):
        success = self._add_identity_unique(user_identities, identity)
        if not success:
            raise UniqueConstraintFailed("Identity must be globally unique")

    def remove_user_by_id(self, id_: str) -> bool:
        if self.user_exist(id_):
            user_record = self._get_user_by_id(id_)
            self._users.remove(user_record)
            self._save()
            user_removed = True
        else:
            user_removed = False
        return user_removed

    def user_exist(self, id_: str) -> bool:
        matches = filter(lambda record: record[JsonAttribute.user][JsonAttribute.id] == id_, self._users)
        return any(matches)

    def get_user_by_id(self, id_: str) -> User:
        user_record = self._get_user_by_id(id_)
        if user_record:
            return self._unserialize_user(user_record[JsonAttribute.user])
        else:
            return NonExistingUser()

    def _get_user_by_id(self, id_: str) -> dict:
        default_value = dict()
        return next((user for user in self._users if user[JsonAttribute.user][JsonAttribute.id] == id_), default_value)

    def get_user_by_name(self, name: str) -> User:
        try:
            user_record = next(user for user in self._users if user[JsonAttribute.user][JsonAttribute.name] == name)
            return self._unserialize_user(user_record[JsonAttribute.user])
        except StopIteration:
            return NonExistingUser()

    def _unserialize_user(self, json_formatted_user) -> User:
        return User(
            json_formatted_user[JsonAttribute.id],
            json_formatted_user[JsonAttribute.name],
            User.Privilege(json_formatted_user[JsonAttribute.privilege]),
        )

    def get_all_users(self) -> list:
        return list(self._unserialize_user(user[JsonAttribute.user]) for user in self._users)

    def add_identity_to_user(self, id_: str, identity: UserIdentity) -> bool:
        user_record = self._get_user_by_id(id_)
        if user_record:
            user_identities = user_record[JsonAttribute.identities]
            identity_added = self._add_identity_unique(user_identities, identity)
            self._save()
        else:
            identity_added = False
        return identity_added

    def _add_identity_unique(self, user_identities: list, identity: UserIdentity) -> bool:
        is_unique = self._is_identity_unique(identity)
        if is_unique:
            user_identities.append(identity)
        return is_unique

    def _is_identity_unique(self, identity: UserIdentity) -> bool:
        user_identities = UserIdentityMappingIterator(self._users)
        matches = filter(lambda mapping: mapping.identity == identity, user_identities)
        return any(matches) == False

    def get_user_by_identity(self, identity: UserIdentity) -> User:
        default_user = NonExistingUser()
        user_identities = UserIdentityMappingIterator(self._users)
        user = next((self._unserialize_user(mapping.user) for mapping in user_identities if mapping.identity == identity), default_user)
        return user

    def __str__(self) -> str:
        return json.dumps(self._users, indent=4)


class UserAccountActivationInMemoryStorage(UserAccountActivationStorage):

    def __init__(self):
        self._new_user_accounts = dict()  # : Dict[str, User]

    def put_user(self, user: User) -> str:
        nonce = self._new_nonce()
        self._new_user_accounts[nonce] = user
        return nonce

    def _new_nonce(self) -> str:
        nonce = uuid.uuid4()
        return nonce.hex

    def pop_user(self, nonce: str) -> User:
        if nonce in self._new_user_accounts:
            user = self._new_user_accounts[nonce]
            del self._new_user_accounts[nonce]
        else:
            user = NonExistingUser()
        return user
