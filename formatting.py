from application import (
    User,
    Host,
    UnixAccount,
)

class UserAttribute:
    """String literals for User attributes used during serialize and unserialize """
    USER_ID, USER_NAME, USER_PRIVILEGE = "id", "name", "privilege"


class JsonFormattedUser(dict):

    def __init__(self, user: User):
        user_data = {
            UserAttribute.USER_ID: user.id,
            UserAttribute.USER_NAME: user.name,
            UserAttribute.USER_PRIVILEGE: user.privilege.value
        }
        super().__init__(user_data)

class HostAttribute:
    """String literals for valid "Host" attributes"""
    HOST_ID, HOST_NAME = "id", "name"


class JsonFormattedHost(dict):

    def __init__(self, host: Host):
        host_data = {
            HostAttribute.HOST_ID: host.id,
            HostAttribute.HOST_NAME: host.name,
        }
        super().__init__(host_data)


class UnixAccountAttribute:
    """String literals for valid "UnixAccount" attributes"""
    UNIX_ACCOUNT_ID, UNIX_ACCOUNT_NAME = "id", "name"


class JsonFormattedUnixAccount(dict):

    def __init__(self, unix_account: UnixAccount):
        unix_account_data = {
            UnixAccountAttribute.UNIX_ACCOUNT_ID: unix_account.id,
            UnixAccountAttribute.UNIX_ACCOUNT_NAME: unix_account.name,
        }
        super().__init__(unix_account_data)

