
class Host:

    def __init__(self, id_: str, name: str):
        self._id = id_
        self._name = name

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

