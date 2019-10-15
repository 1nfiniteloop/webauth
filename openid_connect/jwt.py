from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Callable,
    Dict,
    List
)

from jose import (
    jwt,
    jws,
    JWTError
)


class JwtDecodeFailed(Exception):
    pass


class JWKPublicKeyCache:
    """ Caches public key from well-known endpoint """
    def __init__(self, jwk_pubkey_cb: Callable[[], Dict], update_interval: timedelta = timedelta(hours=12)):
        self._jwk_pubkey_cb = jwk_pubkey_cb
        self._update_interval = update_interval
        self._last_updated = datetime.fromtimestamp(0)
        self._keys = list()

    def key(self, key_id: str) -> Dict:
        return next((key for key in self._get_keys() if key["kid"] == key_id), dict())

    def _get_keys(self) -> List:
        now = datetime.now()
        if self._cache_expired(now):
            self._refresh_cache()
        return self._keys

    def _cache_expired(self, now: datetime) -> bool:
        return now > (self._last_updated + self._update_interval)

    def _refresh_cache(self):
        jwk_pubkeys = self._jwk_pubkey_cb()
        self._last_updated = datetime.now()
        self._keys = jwk_pubkeys["keys"]


class JwtDecoder:

    """ https://openid_provider.net/specs/openid_provider-connect-core-1_0.html#IDTokenValidation """

    def __init__(self, jwk_public_key: JWKPublicKeyCache, issuer: str, client_id: str):
        self._jwk_pkey = jwk_public_key
        self._issuer = issuer
        self._client_id = client_id

    def decode(self, openid_credentials: dict) -> dict:
        try:
            return self._try_decode(openid_credentials)
        except JWTError as err:
            raise JwtDecodeFailed(str(err))

    def _try_decode(self, openid_credentials: dict) -> dict:
        id_token = openid_credentials["id_token"]
        # "access_token" must only be provided if claim is provided, else "jwt.decode" throws...
        if b"at_hash" in jws.get_unverified_claims(id_token):
            access_token = openid_credentials["access_token"]
        else:
            access_token = None
        header = jws.get_unverified_header(id_token)
        verified_id_token = jwt.decode(
            id_token,
            self._jwk_pkey.key(header["kid"]),
            issuer=self._issuer,
            access_token=access_token,
            audience=self._client_id,
        )
        return verified_id_token
