from application.storage import UserAccountActivationStorage


class UserAccountActivationLinkBuilder:

    def __init__(self, template_url: str):
        self._template_url = template_url

    def get_link_from_nonce(self, nonce: str) -> str:
        return self._template_url.format(nonce=nonce)


class UserAccountActivationWithLink:

    def __init__(self, storage: UserAccountActivationStorage, link_builder: UserAccountActivationLinkBuilder):
        self._storage = storage
        self._link_builder = link_builder

    def activate_account_and_get_link(self, user) -> str:
        nonce = self._storage.put_user(user)
        link = self._link_builder.get_link_from_nonce(nonce)
        return link
