from application.storage import HostStorage
from application import Host
from ..response_mixin import StubResponseMixin

stored_host = Host("1234-5678", "hostname")


class HostStorageStub(HostStorage, StubResponseMixin):

    def default_response_data(self) -> dict:
        response_data = {
            "add_host": True,
            "host_exists": False,
            "remove_host_by_id": True,
            "get_host_by_id": stored_host,
            "get_all_hosts": [stored_host]
        }
        return response_data

    def add_host(self, host: Host) -> bool:
        """Returns True if added successfully, False if item already exists"""
        return self.get_response()

    def host_exists(self, id_: str) -> bool:
        return self.get_response()

    def remove_host_by_id(self, id_: str) -> bool:
        """Returns True if is deleted successfully, False if item don't exists"""
        return self.get_response()

    def get_host_by_id(self, id_: str) -> Host:
        return self.get_response()

    def get_all_hosts(self) -> list:
        return self.get_response()
