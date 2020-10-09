import json
import logging
from typing import (
    List,
)
import urllib.parse

import tornado.routing

from application import (
    UserAccountAuthentication,
    UserAccountRegistration,
)
from application.storage import (
    UserAccountStorage
)
from config import (
    OpenIDProviderConfiguration,
)
from http_client import DefaultHttpClient
from openid_connect import (
    OpenIDConfiguration,
    OpenIDClientConfiguration,
    OpenIDEndpointsBuilder,
    TokenFromCodeExchanger,
    TokenFromCodeExchangeBuilder,
    JwtDecoder,
    JWKPublicKeyCache
)
from user_serializer import (
    UserSerializer,
    AuthenticatedUserSerializer
)
from user_account_openid import (
    OpenIDUserAccountAuthentication,
    OpenIDUserAccountRegistration,
)

from ..request_handler import (
    OAuth2Authorization,
    OAuth2AuthorizationArguments,
    UserAccountLoginCallback,
    UserAccountRegistrationCallback,
    UserAccountLogoutOpenID
)
from utils import url_path_join

log = logging.getLogger(__name__)


class RoutesUrl:

    def __init__(self, login_path: str, logout_path, register_path: str):
        self._login_path = login_path
        self._logout_path = logout_path
        self._register_path = register_path

    @property
    def login(self) -> str:
        return self._login_path

    @property
    def logout(self) -> str:
        return self._logout_path

    @property
    def register(self) -> str:
        return self._register_path



def create_routes(
        user_account_storage: UserAccountStorage,
        openid_provider_cfg: OpenIDProviderConfiguration,
        external_url: str,
        token_request_builder: TokenFromCodeExchangeBuilder,
        openid_endpoints_builder: OpenIDEndpointsBuilder,
        routes_url: RoutesUrl,
) -> List[tornado.routing.Rule]:
    """ Creates routes from openid providers in configuration (eg. google, keycloak) """

    provider_name = openid_provider_cfg.name
    log.debug("Fetching well-known file from '{provider}'".format(provider=provider_name))
    well_known = _http_get_json(openid_provider_cfg.well_known)
    openid_config = OpenIDConfiguration(
        openid_endpoints_builder.new(well_known),
        OpenIDClientConfiguration(openid_provider_cfg.client_id, openid_provider_cfg.client_secret)
    )
    jwk_pubkey = _create_jwk_public_keys_cache(openid_config.endpoints.jwks_endpoint)
    builder = OpenIDRoutesBuilder(
        external_url,
        AuthenticatedUserSerializer(),
        openid_config,
        user_account_storage,
        jwk_pubkey,
        token_request_builder
    )
    routes = [
        *builder.get_routes_register(routes_url.register),
        *builder.get_routes_login(routes_url.login),
        builder.get_route_logout(routes_url.logout),
    ]
    return routes


def _create_jwk_public_keys_cache(jwks_endpoint: str) -> JWKPublicKeyCache:
    return JWKPublicKeyCache(jwk_pubkey_cb=lambda: _fetch_jwk_public_keys_cb(jwks_endpoint))


def _fetch_jwk_public_keys_cb(jwks_endpoint: str):
    log.debug("Fetching public key(s) from well-known url: {url}".format(url=jwks_endpoint))
    return _http_get_json(jwks_endpoint)


def _http_get_json(url: str):
    """ Get json from a remote source """
    http_client = DefaultHttpClient()
    body = http_client.get(url)
    return json.loads(body)


class OpenIDRoutesBuilder:
    """ This class offers http endpoints for user authentication and registration with openid connect. """
    def __init__(
            self,
            external_url: str,
            user_serializer: UserSerializer,
            openid_config: OpenIDConfiguration,
            user_storage: UserAccountStorage,
            jwk_pubkey: JWKPublicKeyCache,
            token_request_builder: TokenFromCodeExchangeBuilder
    ):
        url = urllib.parse.urlparse(external_url)
        self._app_base_url = url.geturl()
        self._app_base_path = url.path or "/"
        self._user_serializer = user_serializer
        self._openid_config = openid_config
        self._user_storage = user_storage
        self._jwk_pubkey = jwk_pubkey  # public key from openid openid_client_cfg
        self._token_request_builder = token_request_builder

    def get_routes_login(self, url_path: str, url_path_cb_suffix: str = "/callback") -> list:
        """ Returns routes for user authentication (login and login-callback) """
        callback_path = url_path_join(url_path, url_path_cb_suffix)
        callback_url = url_path_join(url_path, url_path_cb_suffix, base_url=self._app_base_url)
        routes = [
            self._get_oauth2_authorization_route(url_path, callback_url),
            self._get_user_login_route_callback(callback_path, callback_url)
        ]
        return routes

    def get_routes_register(self, url_path: str, url_path_cb_suffix: str = "/callback") -> list:
        """ Returns routes for user registration (login and login-callback) """
        callback_path = url_path_join(url_path, url_path_cb_suffix)
        callback_url = url_path_join(url_path, url_path_cb_suffix, base_url=self._app_base_url)
        routes = [
            self._get_oauth2_authorization_route(url_path, callback_url),
            self._get_user_register_route_callback(callback_path, callback_url)

        ]
        return routes

    def get_route_logout(self, url_path: str) -> tornado.routing.Rule:
        """ Returns route for user logout """
        rule = tornado.routing.Rule(
            tornado.routing.PathMatches(url_path),
            UserAccountLogoutOpenID,
            dict(
                openid_logout_endpoint=self._openid_config.endpoints.logout_endpoint,
                callback_url=self._app_base_url
            )
        )
        return rule

    def _get_oauth2_authorization_route(self, url_path: str, callback_url: str) -> tornado.routing.Rule:
        rule = tornado.routing.Rule(
            tornado.routing.PathMatches(url_path),
            OAuth2Authorization,
            dict(
                user_serializer=self._user_serializer,
                args=self._get_user_auth_args(callback_url)
            )
        )
        return rule

    def _get_user_auth_args(self, callback_url: str) -> OAuth2AuthorizationArguments:
        args = OAuth2AuthorizationArguments(
            callback_url,
            self._app_base_path,
            self._openid_config.endpoints.authorization_endpoint,
            self._openid_config.client_config.client_id
        )
        return args

    def _get_user_login_route_callback(self, url_path: str, callback_url: str) -> tornado.routing.Rule:
        args = dict(
            user_serializer=self._user_serializer,
            token_request=self._get_token_request(callback_url),
            app_base_path=self._app_base_path,
            user_authentication=self._get_user_authentication()
        )
        rule = tornado.routing.Rule(
            tornado.routing.PathMatches(url_path),
            UserAccountLoginCallback,
            args
        )
        return rule

    def _get_user_register_route_callback(self, url_path: str, callback_url: str) -> tornado.routing.Rule:
        args = dict(
            user_serializer=self._user_serializer,
            token_request=self._get_token_request(callback_url),
            app_base_path=self._app_base_path,
            user_registration=self._get_user_registration()
        )
        rule = tornado.routing.Rule(
            tornado.routing.PathMatches(url_path),
            UserAccountRegistrationCallback,
            args
        )
        return rule

    def _get_token_request(self, callback_url: str) -> TokenFromCodeExchanger:
        token_request = self._token_request_builder.new(
            self._openid_config.endpoints.token_endpoint,
            self._openid_config.client_config,
            callback_url,
        )
        return token_request

    def _get_user_authentication(self) -> UserAccountAuthentication:
        user_authentication = OpenIDUserAccountAuthentication(
            self._get_jwt_decoder(),
            self._user_storage
        )
        return user_authentication

    def _get_user_registration(self) -> UserAccountRegistration:
        user_registration = OpenIDUserAccountRegistration(
            self._get_jwt_decoder(),
            self._user_storage
        )
        return user_registration

    def _get_jwt_decoder(self) -> JwtDecoder:
        jwt_decoder = JwtDecoder(
            self._jwk_pubkey,
            self._openid_config.endpoints.issuer,
            self._openid_config.client_config.client_id
        )
        return jwt_decoder
