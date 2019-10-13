from application import (
    User,
    Credentials,
    UserAccountAuthentication,
    UserAccountRegistration
)
from application.storage import (
    UserAccountStorage,
    UserIdentity,
)
from openid_connect import (
    JwtDecoder,
)
from storage import (
    ApplicationUserData,
)


class IDTokenAttribute:
    ISSUER, AUDIENCE, SUBJECT, NAME = "iss", "aud", "sub", "name"


class OpenIdUserIdentity(UserIdentity):

    def __init__(self, issuer: str, client_id: str, user_id: str):
        item = {
            "type": "openid",
            "issuer": issuer,
            "client_id": client_id,
            "user_id": user_id
        }
        super().__init__(item)


class OpenIDUserAccount:

    def __init__(self, user_storage: UserAccountStorage):
        self._user_storage = user_storage

    def _new_identity(self, id_token: dict) -> UserIdentity:
        identity = OpenIdUserIdentity(
            issuer=id_token[IDTokenAttribute.ISSUER],
            client_id=id_token[IDTokenAttribute.AUDIENCE],
            user_id=id_token[IDTokenAttribute.SUBJECT]
        )
        return identity

    def get_user_by_identity(self, id_token: dict) -> User:
        user_identity = self._new_identity(id_token)
        return self._user_storage.get_user_by_identity(user_identity)

    def register_new_user(self, id_token: dict) -> User:
        user_data = ApplicationUserData(name=id_token[IDTokenAttribute.NAME])
        user_identity = self._new_identity(id_token)
        user = self._user_storage.add_user(user_data, user_identity)
        return user

    def register_new_identity(self, user: User, id_token: dict) -> bool:
        user_identity = self._new_identity(id_token)
        return self._user_storage.add_identity_to_user(user.id, user_identity)


class OpenIDUserAccountAuthentication(UserAccountAuthentication):

    def __init__(self, jwt_decoder: JwtDecoder, user_storage: UserAccountStorage):
        self._jwt_decoder = jwt_decoder
        self._user_account = OpenIDUserAccount(user_storage)

    def authenticate(self, credentials: Credentials) -> User:
        decoded_jwt = self._jwt_decoder.decode(credentials)
        user = self._user_account.get_user_by_identity(decoded_jwt)
        return user


class OpenIDUserAccountRegistration(UserAccountRegistration):

    def __init__(self, jwt_decoder: JwtDecoder, user_storage: UserAccountStorage):
        self._jwt_decoder = jwt_decoder
        self._user_account = OpenIDUserAccount(user_storage)

    def register_user(self, openid_credentials: Credentials) -> User:
        id_token = self._jwt_decoder.decode(openid_credentials)
        user = self._user_account.register_new_user(id_token)
        return user

    def register_identity(self, user: User, openid_credentials: Credentials) -> bool:
        id_token = self._jwt_decoder.decode(openid_credentials)
        return self._user_account.register_new_identity(user, id_token)
