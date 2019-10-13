from abc import (
    ABC,
    abstractmethod
)
import enum


class User:

    class Privilege(enum.Enum):
        NONE, USER, ADMINISTRATOR = range(3)

    def __init__(self, id_: str, name: str, privilege: Privilege=Privilege.NONE):
        self._id = id_
        self._name = name
        self._privilege = privilege

    def is_admin(self) -> bool:
        return self.privilege == self.Privilege.ADMINISTRATOR

    def __str__(self):
        return self.name

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def privilege(self) -> Privilege:
        return self._privilege



class UserSerializer(ABC):

    @abstractmethod
    def unserialize(self, raw: str) -> User:
        pass

    @abstractmethod
    def serialize(self, user: User) -> str:
        pass
