from application import User


class UnprivilegedUser(User):

    """ Represents an unprivileged not logged in user """

    def __init__(self):
        super().__init__("", "unprivileged", User.Privilege.NONE)
