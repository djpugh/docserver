import os
from typing import Any
import uuid
from warnings import warn

from itsdangerous import URLSafeSerializer
from pkg_resources import iter_entry_points
from pydantic import BaseModel, Schema, SecretStr, validator
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


AUTH_ENTRYPOINT = 'docserver.auth.providers'


# We need to set the provider config here


class AuthConfig(BaseModel):
    enabled: bool = Schema(os.getenv('DOCSERVER_AUTH_ENABLED', '0'))
    provider_ep: Any = Schema(os.getenv('DOCSERVER_AUTH_PROVIDER', 'aad').lower())
    # How to make work in multi-threaded
    secret: SecretStr = Schema(SecretStr(os.getenv('DOCSERVER_AUTH_SECRET', str(uuid.uuid4()))))
    salt: SecretStr = Schema(SecretStr(os.getenv('DOCSERVER_AUTH_SALT', str(uuid.uuid4()))))

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
        if not hasattr(self, '_provider'):
            super(BaseModel, self).__setattr__('_provider', self.provider_ep.load()[0]())
        return self._provider

    @property
    def provider_object(self):
        if not hasattr(self, '_provider_object'):
            super(BaseModel, self).__setattr__('_provider_object', self.provider_ep.load()[1]())
        return self._provider_object

    @property
    def serializer(self):
        return URLSafeSerializer(self.secret.get_secret_value(), salt=self.salt.get_secret_value())

    def set_middleware(self, app):
        if self.enabled:
            from docserver.auth.providers.test import TestProvider

            if isinstance(self.provider_object, TestProvider):
                warn('TestAuthBackend is not suitable for production environments')

            def on_auth_error(request: Request, exc: Exception):
                return RedirectResponse('/login')

            app.add_middleware(AuthenticationMiddleware, backend=self.provider_object, on_error=on_auth_error)
            app.add_middleware(SessionMiddleware, secret_key=self.provider.session_secret)
