from abc import (
    ABC,
    abstractmethod
)
import http.client
import urllib.parse

import tornado.httpclient


class HttpRequestFailed(Exception):
    pass


class HttpClient(ABC):

    @abstractmethod
    def get(self, url: str) -> str:
        pass

    @abstractmethod
    def post(self, url: str, body: str, header: dict = None) -> str:
        pass


class AsyncHttpClient(ABC):

    @abstractmethod
    async def get(self, url: str) -> str:
        pass

    @abstractmethod
    async def post(self, url: str, body: str, header: dict = None) -> str:
        pass


class DefaultHttpClient(HttpClient):

    def _get_http_client(self, url):
        if url.scheme == "http":
            cli = http.client.HTTPConnection(url.netloc)
        elif url.scheme == "https":
            cli = http.client.HTTPSConnection(url.netloc)
        else:
            raise http.client.HTTPException("Unsupported protocol scheme: {scheme}".format(scheme=url.scheme))
        return cli

    def get(self, complete_url: str) -> str:
        """ Using native http client """
        url = urllib.parse.urlparse(complete_url)
        http_conn = self._get_http_client(url)
        http_conn.request("GET", url.path)
        response = http_conn.getresponse()
        body = response.read()
        if response.status == 200:
            return body.decode("utf8")
        else:
            raise HttpRequestFailed("HTTP request returned code {code}: {body}".format(
                code=response.code,
                body=body
            ))

    def post(self, url: str, body: str, header: dict = None):
        pass


class TornadoAsyncHttpClient(AsyncHttpClient):

    def _get_http_client(self):
        return tornado.httpclient.AsyncHTTPClient()

    async def get(self, url: str) -> str:
        raise NotImplementedError("TODO!")

    async def post(self, url: str, body: str, header: dict = None) -> str:
        http_client = self._get_http_client()
        response = await http_client.fetch(
            url,
            method="POST",
            headers=header,
            body=body,
            raise_error=False,
        )
        if response.code == 200:
            return response.body
        else:
            raise HttpRequestFailed("HTTP request returned code {code}: {body}".format(
                code=response.code,
                body=response.body
            ))
