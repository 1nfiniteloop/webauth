from abc import (
    ABC,
    abstractmethod,
)

import tornado.web

from application import User


AUTH_TOKEN_NAME = "auth_token"
SESSION_TOKEN_NAME = "user_session"


class AuthenticatedUserBase(tornado.web.RequestHandler, ABC):

    def get_current_user(self) -> User:
        client_cookie = self.get_secure_cookie(AUTH_TOKEN_NAME)
        return self.get_authenticated_user(client_cookie)

    @abstractmethod
    def get_authenticated_user(self, client_cookie: str) -> User:
        pass


def administrator(method):
    """ Decorator for allow only users with administrator privileges to access a resource """
    def wrapper(self, *args, **kwargs):
        if self.current_user.privilege == User.Privilege.ADMINISTRATOR:
            return method(self, *args, **kwargs)
        else:
            raise tornado.web.HTTPError(401)
    return wrapper


def authenticated(method):
    """ Decorator for allow only authenticated users to access a resource """
    def wrapper(self, *args, **kwargs):
        if self.current_user.privilege == User.Privilege.NONE:
            raise tornado.web.HTTPError(401)
        else:
            return method(self, *args, **kwargs)
    return wrapper
