import logging

import tornado.web

from unix_account_authorization import (
    AuthorizationRequestSubject,
    AuthorizationRequest,
    AuthorizationState
)

log = logging.getLogger(__name__)


class SslCertificate:

    class Subject:
        COMMON_NAME = "commonName"  # ...

    def __init__(self, cert: dict):
        """ What's returned from "[tornado.web.RequestHandler].request.get_ssl_certificate()", or natively "getpeercert()" in pyopenssl """
        self._cert = cert

    def get_subject_parameter(self, parameter: str) -> str:
        subject = dict(item[0] for item in self._cert.get("subject", tuple()))
        return subject.get(parameter)


class Parameter(object):
    UNIX_ACCOUNT_ID, SERVICE = "unix_account_id", "service"


class UnixAccountAuthorization(tornado.web.RequestHandler):

    """ This http handler uses client + server certificates to authenticate """

    def initialize(self, auth: AuthorizationRequest):
        self._auth = auth

    async def post(self):
        host_id = self._get_host_id()
        user_id = self.get_argument(Parameter.UNIX_ACCOUNT_ID)
        service_name = self.get_argument(Parameter.SERVICE)
        if not user_id.isnumeric():
            raise tornado.web.HTTPError(400)
        resp = await self._auth.authorize(AuthorizationRequestSubject(
            host_id,
            int(user_id),
            service_name
        ))
        if resp.state == AuthorizationState.AUTHORIZED:
            self.set_status(200)
        elif resp.state == AuthorizationState.UNAUTHORIZED:
            self.set_status(401)
        elif resp.state == AuthorizationState.EXPIRED:
            self.set_status(408)
        else:
            self.set_status(400, reason=resp.message)

    def _get_host_id(self) -> str:
        """ Exracts host id from client ssl certificate Common Name """
        client_cert = self.request.get_ssl_certificate()
        if client_cert:
            ssl_cert = SslCertificate(client_cert)
            host_id = ssl_cert.get_subject_parameter(ssl_cert.Subject.COMMON_NAME)
        else:
            host_id = ""
            log.error("host_id lookup failed, no client certificate provided")
        return host_id
