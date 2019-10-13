from application.storage import IOStorage


class IOStorageStub(IOStorage):

    def read(self) -> str:
        return "[]"

    def write(self, data: str):
        pass
