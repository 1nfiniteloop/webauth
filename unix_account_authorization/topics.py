
def topic_user_requests(user_id: str) -> str:
    return "/user/{id}/request".format(id=user_id)


def topic_user_updates(user_id: str) -> str:
    return "/user/{id}/update".format(id=user_id)


def topic_user_responses(user_id: str) -> str:
    return "/user/{id}/response".format(id=user_id)
