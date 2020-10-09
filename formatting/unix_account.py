from application import UnixAccount


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
