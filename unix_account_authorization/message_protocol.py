from abc import (
    ABC,
    abstractmethod
)
import json

from application.messaging import Message

from .messages import (
    AuthorizationRequestMessage,
    AuthorizationResponseMessage,
    AuthorizationUpdateMessage,
)
from .state import (
    AuthorizationState,
    new_authorization_state,
    UnknownState
)


class JsonAttribute:
    """ String literals for json attributes (don't repeat yourself) """
    TYPE, ID, STATE, HOSTNAME, SERVICE_NAME, UNIX_ACCOUNT_NAME, ERROR_TEXT = "type", "id", "state", "hostname", "service_name", "unix_account_name", "error_text"


class MessageType:
    REQUEST, RESPONSE, UPDATE, ERROR = "authorization_request", "authorization_response", "authorization_update", "error"


class DecodeFailed(Exception):
    """ Raised when decode errors occurs """
    pass


class JsonEncodedErrorResponse(dict):

    def __init__(self, error_text: str):
        data = {
            JsonAttribute.TYPE: "error",
            JsonAttribute.ERROR_TEXT: error_text
        }
        super().__init__(data)


class JsonEncodedAuthorizationRequest(dict):

    def __init__(self, req: AuthorizationRequestMessage):
        message = {
            JsonAttribute.TYPE: MessageType.REQUEST,
            JsonAttribute.ID: req.id,
            JsonAttribute.UNIX_ACCOUNT_NAME: req.unix_account_name,
            JsonAttribute.HOSTNAME: req.host_name,
            JsonAttribute.SERVICE_NAME: req.service_name
        }
        super().__init__(message)


class JsonEncodedAuthorizationUpdate(dict):

    def __init__(self, update: AuthorizationUpdateMessage):
        message = {
            JsonAttribute.TYPE: MessageType.UPDATE,
            JsonAttribute.ID: update.id,
            JsonAttribute.STATE: update.state.name
        }
        super().__init__(message)


def decode_json_response_message(json_fmt_msg: dict) -> AuthorizationResponseMessage:
    try:
        request_id = json_fmt_msg[JsonAttribute.ID]
        state = new_authorization_state(json_fmt_msg[JsonAttribute.STATE])
        return AuthorizationResponseMessage(request_id, state)
    except KeyError as key_name:
        raise DecodeFailed("Bad message format: {key_err}".format(key_err=key_name))
    except UnknownState as err:
        raise DecodeFailed("Bad message format: {err}".format(err=str(err)))


class MessageProtocol(ABC):

    @abstractmethod
    def decode(self, data: str) -> Message:
        pass

    @abstractmethod
    def encode(self, msg: Message) -> str:
        pass

    @abstractmethod
    def encode_error(self, error_text: str) -> str:
        """ Used to propagate an error response from upper layers """
        pass


class WebsocketMessageProtocol(MessageProtocol):

    def decode(self, data: str) -> Message:
        return self._try_decode(data)

    def _try_decode(self, data: str) -> Message:
        try:
            json_decoded_message = json.loads(data)
            return self._try_convert_to_supported_message(json_decoded_message)
        except json.JSONDecodeError:
            raise DecodeFailed("Bad formatted message (not JSON)")
        except KeyError as err:
            raise DecodeFailed("Bad formatted message: {err}".format(err=err))

    def _try_convert_to_supported_message(self, json_fmt_msg: dict) -> Message:
        msg_type = json_fmt_msg[JsonAttribute.TYPE]
        if msg_type == MessageType.RESPONSE:
            return decode_json_response_message(json_fmt_msg)
        else:
            raise DecodeFailed("Unsupported message type")

    def encode(self, msg: Message) -> str:
        msg_type = type(msg)
        if msg_type is AuthorizationRequestMessage:
            encoded_data = json.dumps(JsonEncodedAuthorizationRequest(msg))
        elif msg_type is AuthorizationUpdateMessage:
            encoded_data = json.dumps(JsonEncodedAuthorizationUpdate(msg))
        else:
            encoded_data = ""
        return encoded_data

    def encode_error(self, error_text: str) -> str:
        return json.dumps(JsonEncodedErrorResponse(error_text))
