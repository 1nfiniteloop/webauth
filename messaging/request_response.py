from abc import (
    ABC,
    abstractmethod
)
# TODO remove tornado dependency
# use condition from asyncio:https://docs.python.org/3/library/asyncio-sync.html#asyncio.Condition
# from asyncio import Condition
from tornado.locks import Condition
from datetime import (
    datetime,
    timedelta
)
import enum
import logging
from typing import (
    Any,
    Callable,
    List
)
from application.messaging import (
    Message,
    Observer
)
from .message_bus import (
    MessageBus,
)

log = logging.getLogger(__name__)


class SendPolicy(enum.Enum):
    ALL, AT_LEAST_ONE = range(2)


class State(enum.Enum):
    """ Carries the current state of the request/response"""
    REQUEST_SENT, EXPIRED, RESPONSE_RECEIVED = range(3)


class AwaitableState:

    def __init__(self, initial_state: State = State.REQUEST_SENT):
        self._cond = Condition()
        self._state = initial_state

    def get(self) -> State:
        return self._state

    def set(self, state: State):
        self._set(state)
        self._cond.notify()

    def _set(self, state: State):
        log.debug("State changed to: {state}".format(state=state.name))
        self._state = state

    async def wait_for_state_change(self, expires: timedelta):
        """ Returns true if state has changed, or false on timeouts """
        state_changed = await self._cond.wait(timeout=expires)
        if not state_changed:
            self._set(State.EXPIRED)
        return state_changed


class ResponseObserver(Observer):

    def __init__(self, shared_state: AwaitableState, on_response_received: Callable[[Message], Any]):
        self._shared_state = shared_state
        self._on_response_received = on_response_received

    def on_notify(self, message: Message):
        current_state = self._shared_state.get()
        if current_state not in (State.RESPONSE_RECEIVED, State.EXPIRED):
            self._shared_state.set(State.RESPONSE_RECEIVED)
            self._on_response_received(message)


class ResponseCallback(ABC):

    @abstractmethod
    def on_response(self, msg: Message):
        """ Implement this to handle responses """
        pass

    @abstractmethod
    def on_expired(self):
        """ Implement this to handle timeouts """
        pass


class Request:

    def __init__(self, msg_bus: MessageBus, response: ResponseCallback, request_topics: List[str], response_topics: List[str], policy: SendPolicy = SendPolicy.AT_LEAST_ONE):
        self._msg_bus = msg_bus
        self._response = response
        self._request_topics = request_topics
        self._response_topics = response_topics
        self._policy = policy

    async def send(self, msg: Message, expiration_timestamp: datetime) -> bool:
        """ return if request got sent successfully, according to policy """
        shared_state = AwaitableState()
        response_observer = ResponseObserver(shared_state, self._response.on_response)
        self._subscribe_on_responses(response_observer)
        success_sent = self._publish_request(msg)
        if success_sent:
            state_changed = await shared_state.wait_for_state_change(expiration_timestamp - datetime.now())
            if not state_changed:
                self._response.on_expired()
        self._unsubscribe_on_responses(response_observer)
        return success_sent

    def _subscribe_on_responses(self, response_observer: Observer):
        for topic in self._response_topics:
            self._msg_bus.subscribe(response_observer, topic)

    def _unsubscribe_on_responses(self, response_observer: Observer):
        self._msg_bus.unsubscribe_all(response_observer)

    def _publish_request(self, msg: Message):
        status = list()
        for topic in self._request_topics:
            status.append(self._msg_bus.publish(topic, msg))
        success = self._evaluate_send_status(status)
        if not success:
            log.debug("Send request failed for policy {policy} on {topic_count} topic(s)".format(
                policy=self._policy.name,
                topic_count=len(self._request_topics),
            ))
        return success

    def _evaluate_send_status(self, status: list) -> bool:
        if self._policy == SendPolicy.AT_LEAST_ONE:
            return any(status)
        elif self._policy == SendPolicy.ALL:
            return all(status)
        else:
            log.error("Unknown send policy: {policy_name}".format(policy_name=self._policy.name))
            return False
