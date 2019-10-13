from abc import (
    ABC,
    abstractmethod
)
import inspect


class StubResponseMixin(ABC):

    def __init__(self):
        self._response_data = self.default_response_data()

    def reset_stub(self):
        self._response_data = self.default_response_data()

    @abstractmethod
    def default_response_data(self) -> dict:
        pass

    def set_response_data_for(self, function_name: str, value):
        if function_name in self._response_data:
            self._response_data[function_name] = value
        else:
            raise Exception("Invalid function name: {name}".format(name=function_name))

    def get_response(self):
        """ Magic function which inspects the callers function name and return its response """
        call_stack = inspect.stack()
        parent_stack_frame = call_stack[1]
        return self._response_data[parent_stack_frame.function]
