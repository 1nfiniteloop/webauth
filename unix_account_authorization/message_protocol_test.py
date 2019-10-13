import json
import unittest

from .messages import (
    AuthorizationRequestMessage,
    AuthorizationUpdateMessage,
)

from .message_protocol import (
    WebsocketMessageProtocol,
    JsonAttribute,
    MessageType,
    DecodeFailed
)
from .state import AuthorizationState



class TestWebsocketMessageProtocolDecoding(unittest.TestCase):

    def test_decode_not_json(self):
        proto = WebsocketMessageProtocol()
        with self.assertRaisesRegex(DecodeFailed, "^Bad formatted message"):
            msg = proto.decode("not json")

    def test_decode_message_when_type_missing(self):
        proto = WebsocketMessageProtocol()
        expected_content = {
            "asd": "123",
        }
        with self.assertRaisesRegex(DecodeFailed, "^Bad formatted message"):
            msg = proto.decode(json.dumps(expected_content))

    def test_decode_unknown_message_type(self):
        proto = WebsocketMessageProtocol()
        with self.assertRaisesRegex(DecodeFailed, "^Unsupported message type"):
            msg = proto.decode(json.dumps({
                JsonAttribute.TYPE: "unsupported-type"
            }))

    def test_decode_unknown_message_attribute(self):
        proto = WebsocketMessageProtocol()
        expected_content = {
            JsonAttribute.TYPE: MessageType.RESPONSE,
            "asd": "123",
        }
        with self.assertRaisesRegex(DecodeFailed, "^Bad message format"):
            msg = proto.decode(json.dumps(expected_content))

    def test_decode_unknown_message_state(self):
        proto = WebsocketMessageProtocol()
        expected_content = {
            JsonAttribute.TYPE: MessageType.RESPONSE,
            JsonAttribute.STATE: "UNSUPPORTED_STATE",
        }
        with self.assertRaisesRegex(DecodeFailed, "^Bad message format"):
            msg = proto.decode(json.dumps(expected_content))

    def test_decode_response_message(self):
        proto = WebsocketMessageProtocol()
        expected_content = {
            JsonAttribute.TYPE: MessageType.RESPONSE,
            JsonAttribute.ID: "12345",
            JsonAttribute.STATE: AuthorizationState.UNAUTHORIZED.name
        }
        msg = proto.decode(json.dumps(expected_content))
        self.assertEqual(msg.id, "12345")
        self.assertEqual(msg.state, AuthorizationState.UNAUTHORIZED)


class UnknownMessage:
    pass


class TestWebsocketMessageProtocolEncoding(unittest.TestCase):

    def test_encode_unknown_message(self):
        proto = WebsocketMessageProtocol()
        data = proto.encode(UnknownMessage())
        self.assertFalse(data)

    def test_encode_request_message(self):
        proto = WebsocketMessageProtocol()
        req = AuthorizationRequestMessage("unix-username", "hostname", "login")
        data = proto.encode(req)
        decoded_msg = json.loads(data)
        expected_resp = {
            JsonAttribute.TYPE: MessageType.REQUEST,
            JsonAttribute.ID: req.id,
            JsonAttribute.UNIX_ACCOUNT_NAME: req.unix_account_name,
            JsonAttribute.HOSTNAME: req.host_name,
            JsonAttribute.SERVICE_NAME: req.service_name
        }
        self.assertEqual(decoded_msg, expected_resp)

    def test_encode_update_message(self):
        proto = WebsocketMessageProtocol()
        update = AuthorizationUpdateMessage("1234-5678", AuthorizationState.EXPIRED)
        data = proto.encode(update)
        decoded_msg = json.loads(data)
        expected_resp = {
            JsonAttribute.TYPE: MessageType.UPDATE,
            JsonAttribute.ID: update.id,
            JsonAttribute.STATE: update.state.name
        }
        self.assertEqual(decoded_msg, expected_resp)

    def test_encode_error(self):
        expected_error_msg = "Oops, errror!"
        proto = WebsocketMessageProtocol()
        data = proto.encode_error(expected_error_msg)
        decoded_msg = json.loads(data)
        expected_resp = {
            JsonAttribute.TYPE: MessageType.ERROR,
            JsonAttribute.ERROR_TEXT: expected_error_msg
        }
        self.assertEqual(decoded_msg, expected_resp)


if __name__ == "__main__":
    unittest.main()
