import json

from application import Host
from application.storage import (
    HostStorage,
    NonExistingHost,
    IOStorage
)



class JsonAttribute:
    """  String literals for all json attributes (don't repeat yourself) """
    name, id = "name", "id"


class JsonFormattedHostStorage(HostStorage):

    class JsonFormattedHost(dict):

        def __init__(self, host: Host):
            data = {
                JsonAttribute.name: host.name,
                JsonAttribute.id: host.id
            }
            super().__init__(data)

    def __init__(self, storage: IOStorage):
        self._storage = storage
        self._hosts = self._load()

    def _load(self) -> list:
        try:
            data = self._storage.read()
            hosts = json.loads(data)
        except FileNotFoundError:
            hosts = list()
        return hosts

    def _save(self):
        data = json.dumps(self._hosts, indent=4)
        self._storage.write(data)

    def add_host(self, host: Host) -> bool:
        """Returns True if added successfully, False if item already exists"""
        if self.host_exists(host.id):
            host_added = False
        else:
            self._hosts.append(self.JsonFormattedHost(host))
            self._save()
            host_added = True
        return host_added

    def host_exists(self, id_: str) -> bool:
        matches = filter(lambda host: host[JsonAttribute.id] == id_, self._hosts)
        return any(matches)

    def remove_host_by_id(self, id_: str) -> bool:
        """Returns True if is deleted successfully, False if item don't exists"""
        host = self._get_host_by_id(id_)
        if host:
            self._hosts.remove(host)
            self._save()
            host_removed = True
        else:
            host_removed = False
        return host_removed

    def get_host_by_id(self, id_: str) -> Host:
        host = self._get_host_by_id(id_)
        if host:
            return self._unserialize_host(host)
        else:
            return NonExistingHost()

    def _get_host_by_id(self, id_: str) -> dict:
        default_value = dict()
        return next((host for host in self._hosts if host[JsonAttribute.id] == id_), default_value)

    def get_all_hosts(self) -> list:
        hosts = list(self._unserialize_host(host) for host in self._hosts)
        return hosts

    def _unserialize_host(self, json_formatted_host: dict) -> Host:
        host = Host(
            json_formatted_host[JsonAttribute.id],
            json_formatted_host[JsonAttribute.name]
        )
        return host

    def __str__(self) -> str:
        return json.dumps(self._hosts, indent=4)
