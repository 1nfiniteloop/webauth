from .base import (
    AuthenticatedUserBase,
    administrator
)
from application import (
    Host,
    User,
    UserSerializer
)
from formatting import JsonFormattedHost
from storage import (
    HostStorage
)

class Parameter(object):
    """ Valid parameters in http requests """
    HOSTNAME, HOST_ID = ("hostname", "host_id")


class HostAdministrationArguments:

    def __init__(self, user_serializer: UserSerializer, storage: HostStorage):
        self._storage = storage
        self._user_serializer = user_serializer

    @property
    def storage(self) -> HostStorage:
        return self._storage

    @property
    def user_serializer(self) -> UserSerializer:
        return self._user_serializer


class HostAdministration(AuthenticatedUserBase):

    def initialize(self, args: HostAdministrationArguments):
        self._args = args

    def get_authenticated_user(self, client_cookie: str) -> User:
        return self._args.user_serializer.unserialize(client_cookie)

    @administrator
    def post(self):
        """ Register a new host """
        hostname = self.get_argument(Parameter.HOSTNAME)
        host_id = self.get_argument(Parameter.HOST_ID)
        host_added = self._args.storage.add_host(Host(host_id, hostname))
        if not host_added:
            self.set_status(400)

    @administrator
    def delete(self):
        """ Unregister an existing host """
        host_id = self.get_argument(Parameter.HOST_ID)
        host_deleted = self._args.storage.remove_host_by_id(host_id)
        if not host_deleted:
            self.set_status(400)

    @administrator
    def get(self):
        if Parameter.HOST_ID in self.request.arguments:
            host_id = self.get_argument(Parameter.HOST_ID)
            host = self._args.storage.get_host_by_id(host_id)
            hosts = list()
            if host.id:  # database could return "NonexistingHost"
                hosts.append(JsonFormattedHost(host))
        else:
            hosts = list(JsonFormattedHost(host) for host in self._args.storage.get_all_hosts())
        self.write({
            "hosts": hosts
        })
