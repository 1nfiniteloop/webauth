from application.messaging import Message


def filter_by_type(method):
    """ Decorator for passing through messages by specific type, declared in type hints """
    desired_type = method.__annotations__["message"]

    def wrapper(self, msg: Message):
        if type(msg) is desired_type:
            method(self, msg)
    return wrapper
