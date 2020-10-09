import ssl


class SSLContext(object):

    """ Ref: http://www.tornadoweb.org/en/stable/httputil.html?highlight=httpserverrequest#tornado.httputil.HTTPServerRequest.get_ssl_certificate """

    def __init__(self, cert: str, key: str, cacert: str):
        self._cert = cert
        self._key = key
        self._cacert = cacert

    @property
    def client_auth(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(self._cert, self._key)
        context.load_verify_locations(self._cacert)
        return context

    @property
    def server_auth(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(self._cert, self._key)
        context.load_verify_locations(self._cacert)
        return  context
