from application.storage import IOStorage


class FileStorage(IOStorage):

    def __init__(self, file_name: str):
        self._file_name = file_name

    def read(self) -> str:
        with open(self._file_name, "r") as file:
            data = file.read()
        return data

    def write(self, data: str):
        with open(self._file_name, "w") as file:
            file.write(data)
