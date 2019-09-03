import os
from typing import Any
import uuid
from warnings import warn

from itsdangerous import URLSafeSerializer
from pkg_resources import iter_entry_points
from pydantic import BaseModel, Schema, SecretStr, validator
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware

from docserver.auth.providers.test import TestProvider

AUTH_ENTRYPOINT = 'docserver.auth.providers'


# We need to set the provider config here


class AuthConfig(BaseModel):
    enabled: bool = Schema(os.getenv('DOCSERVER_AUTH_ENABLED', '0'))
    provider_ep: Any = Schema(os.getenv('DOCSERVER_AUTH_PROVIDER', 'aad').lower())
    # How to make work in multi-threaded
    secret: SecretStr = Schema(SecretStr(os.getenv('DOCSERVER_SECRET', str(uuid.uuid4()))))

    @validator('enabled', pre=True, always=True)
    def validate_enabled(cls, value):
        return str(value).lower() in ['1', 'true']

    @validator('provider_ep', pre=True, always=True, check_fields=False)
    def validate_provider(cls, value):
        entrypoints = {ep.name.lower(): ep for ep in iter_entry_points(AUTH_ENTRYPOINT) if ep.name is not None}
        try:
            return entrypoints[value.lower()]
        except KeyError:
            raise ValueError(f'{value} not found in {list(entrypoints.keys())}')

    @property
    def provider(self):
        return self.provider_ep.load()[0]

    @property
    def provider_class(self):
        return self.provider_ep.load()[1]

    @property
    def serializer(self):
        return URLSafeSerializer(self.session_secret, salt=self.session_salt)

    def set_middleware(self, app):
        if self.enabled:
            if TestProvider in self.provider_class.__mro__:
                warn('TestAuthBackend is not suitable for production environments')
            app.add_middleware(AuthenticationMiddleware, backend=self.provider_class)
            app.add_middleware(SessionMiddleware, secret_key=self.provider.session_secret)
