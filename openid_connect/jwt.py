from jose import (
    jwt,
    jws,
    JWTError
)


class JwtDecodeFailed(Exception):
    pass


# NOTE: this might need to have the capability yo update periodically since google switches keys each day
class JWKPublicKey:
    """ Fetches public key from well-known endpoint """
    def __init__(self, jwk_pubkeys: dict):
        self._keys = jwk_pubkeys["keys"]

    def rsa(self, key_id: str) -> dict:
        try:
            return next(key for key in self._keys if key["kid"] == key_id)
        except StopIteration:
            return dict()


class JwtDecoder:

    """ https://openid_provider.net/specs/openid_provider-connect-core-1_0.html#IDTokenValidation """

    def __init__(self, jwk_public_key: JWKPublicKey, issuer: str, client_id: str):
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
            self._jwk_pkey.rsa(header["kid"]),
            issuer=self._issuer,
            access_token=access_token,
            audience=self._client_id,
        )
        return verified_id_token
