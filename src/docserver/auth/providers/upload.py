"""Upload Token handlers."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from authlib.jose import jwt
from fastapi_aad_auth._base.provider import Provider
from fastapi_aad_auth._base.validators import TokenValidator
from fastapi_aad_auth.utilities import DeprecatableFieldsMixin, expand_doc
from pydantic import BaseSettings as _BaseSettings, Field, PrivateAttr, SecretStr

from docserver.auth.user import APIUser
from docserver.permissions import DEFAULTS as PERMISSIONS_DEFAULTS


_DEFAULT_LIFETIME = 60*15  # 15 minutes


class BaseSettings(DeprecatableFieldsMixin, _BaseSettings):
    """Base Settings with Deprecatable Fields."""
    pass


class UploadBearerTokenValidator(TokenValidator):
    """Validator for Bearer token based authentication."""

    def __init__(self, token_secret: str, default_write_permission: str = PERMISSIONS_DEFAULTS['write'], token_lifetime: int = _DEFAULT_LIFETIME):
        super().__init__('', '', '')
        self._default_write_permission = default_write_permission
        self._token_lifetime = token_lifetime
        self._token_secret = token_secret

    def create_token(self, scopes=None):
        if not scopes:
            scopes = [f'{self._default_write_permission}/write']
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=self._token_lifetime)
        payload = {'iss': 'docserver',
                   'nbf': now - timedelta(seconds=30),
                   'exp': expires,
                   'iat': now,
                   'scopes': scopes,
                   }
        token = jwt.encode({'alg': 'HS256', 'kid': None}, payload, str(self._token_secret))
        return token, expires

    def _decode_token(self, token):
        claims = jwt.decode(token, str(self._token_secret))
        return claims

    @property
    def _claims_options(self):
        options = {"iss": {"essential": True, "value": 'docserver'},
                   "exp": {"essential": True},
                   "nbf": {"essential": True},
                   "iat": {"essential": True},
                   "scopes": {"essential": True}}
        return options

    def _get_user_from_claims(self, claims):
        return APIUser(permissions=claims['scopes'])


class UploadBearerProvider(Provider):
    def __init__(self, token_secret: str, default_write_permission: str, token_lifetime: int = _DEFAULT_LIFETIME):
        token_validator = UploadBearerTokenValidator(token_secret, default_write_permission, token_lifetime)
        super().__init__(validators=[token_validator], authenticator=None, enabled=True)

    def get_routes(self, *args, **kwargs):
        return []

    def create_token(self, scopes):
        return self.validators[0].create_token(scopes)

    @classmethod
    def from_config(cls, session_validator, config, provider_config, user_klass: Optional[type] = None):
        """Load the auth backend from a config.

        Args:
            session_validator (SessionValidator): the session validator to use
            config: Loaded configuration

        Keyword Args:
            user_klass: The class to use as a user
        """
        del session_validator
        del user_klass
        token_secret = provider_config.token_secret
        if token_secret is not None:
            token_secret = token_secret.get_secret_value()  # type: ignore

        return cls(token_secret=token_secret, default_write_permission=provider_config.default_write_permission,
                   token_lifetime=provider_config.token_lifetime)

    def get_login_button(self, *args, **kwargs):
        return ''


@expand_doc
class UploadBearerConfig(BaseSettings):
    token_secret: SecretStr = Field(str(uuid.uuid4()), env='DOCSERVER_UPLOAD_TOKEN_SECRET')
    token_lifetime: int = Field(_DEFAULT_LIFETIME, env='DOCSERVER_UPLOAD_TOKEN_LIFETIME')
    default_write_permission: str = Field(PERMISSIONS_DEFAULTS['write'])
    _provider_klass: type = PrivateAttr(UploadBearerProvider)


entrypoint = (UploadBearerConfig, UploadBearerProvider)
