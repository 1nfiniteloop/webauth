import tornado.web

from .base import (
    AUTH_TOKEN_NAME,
    SESSION_TOKEN_NAME,
)

class UserAccountLogout(tornado.web.RequestHandler):

    def initialize(self, callback_url: str = "/"):
        self._callback_url = callback_url

    def get(self):
        self.clear_cookie(AUTH_TOKEN_NAME)
        self.clear_cookie(SESSION_TOKEN_NAME)
        self.redirect(self._callback_url)
