from application.storage import Storage
from config import (
    StorageConfiguration,
)
from storage import (
    FileStorage,
    JsonFormattedUserAccountStorage,
    JsonFormattedHostStorage,
    JsonFormattedUnixAccountStorage,
    UserAccountActivationInMemoryStorage
)


def create_storage(config: StorageConfiguration) -> Storage:
    storage = Storage(
        JsonFormattedHostStorage(FileStorage(config.hosts_filename)),
        JsonFormattedUserAccountStorage(FileStorage(config.user_accounts_filename)),
        JsonFormattedUnixAccountStorage(FileStorage(config.unix_accounts_filename)),
        UserAccountActivationInMemoryStorage()
    )
    return storage
