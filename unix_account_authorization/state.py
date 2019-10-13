from enum import Enum


class UnknownState(Exception):
    pass


class AuthorizationState(Enum):
    WAITING, EXPIRED, AUTHORIZED, UNAUTHORIZED, ERROR = range(5)


def new_authorization_state(state_name: str) -> AuthorizationState:
    try:
        value = next(state.value for state in AuthorizationState if state.name == state_name)
        return AuthorizationState(value)
    except StopIteration:
        raise UnknownState("State '{name}' unknown".format(name=state_name))
