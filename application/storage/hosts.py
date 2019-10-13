from abc import (
    ABC,
    abstractmethod
)

from ..host import Host


class NonExistingHost(Host):
    """ Represents a non-existing host returned when no record found in database, identified by an empty id """
    def __init__(self):
        super().__init__(id_="", name="nonexisting-host")


class HostStorage(ABC):

    @abstractmethod
    def add_host(self, host: Host) -> bool:
        """Returns True if added successfully, False if item already exists"""
        pass

    @abstractmethod
    def host_exists(self, id_: str) -> bool:
        pass

    @abstractmethod
    def remove_host_by_id(self, id_: str) -> bool:
        """Returns True if is deleted successfully, False if item don't exists"""
        pass

    @abstractmethod
    def get_host_by_id(self, id_: str) -> Host:
        pass

    @abstractmethod
    def get_all_hosts(self) -> list:
        pass
