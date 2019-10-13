from application import User
from application.storage import (
    UserAccountStorage,
    UserIdentity,
)
from storage import (
    ApplicationUserData
)
from ..response_mixin import StubResponseMixin

stored_user = User(id_="123-456-789", name="User from database")


class UserAccountStorageStub(UserAccountStorage, StubResponseMixin):

    def default_response_data(self) -> dict:
        response_data = {
            "add_user": stored_user,
            "user_exist": False,
            "remove_user_by_id": True,
            "get_user_by_id": stored_user,
            "get_user_by_name": stored_user,
            "get_all_users": [stored_user],
            "add_identity_to_user": True,
            "get_user_by_identity": stored_user
        }
        return response_data

    def add_user(self, user: ApplicationUserData, identity: UserIdentity = None) -> User:
        """  Return a user based on the data provided """
        return User("123-456-789", user["name"], User.Privilege(user["privilege"]))
        # return self.get_response()

    def user_exist(self, id_: str) -> bool:
        return self.get_response()

    def remove_user_by_id(self, id_: str) -> bool:
        """Returns True if user is deleted successfully, False if user don't exists"""
        return self.get_response()

    def get_user_by_id(self, id_: str) -> User:
        return self.get_response()

    def get_user_by_name(self, name: str) -> User:
        return self.get_response()

    def get_all_users(self) -> list:
        return self.get_response()

    def add_identity_to_user(self, id_: str, identity: UserIdentity) -> bool:
        """ Returns true if user exists and identity don't already exist """
        return self.get_response()

    def get_user_by_identity(self, identity: UserIdentity) -> User:
        return self.get_response()
