from application import Credentials


class PasswordCredentials(Credentials):

    class Keys:
        USERNAME, PASSWORD = "username", "password"

    def __init__(self, username, password):
        credentials = {
            self.Keys.USERNAME: username,
            self.Keys.PASSWORD: password
        }
        super().__init__(credentials)
