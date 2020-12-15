"""Application Configuration."""
import logging
import os
from typing import Optional, Union
import uuid

from fastapi_aad_auth import __version__ as fastapi_aad_auth_version, Config as _AuthConfig  # noqa: F401
from fastapi_aad_auth.config import LoginUIConfig
from fastapi_aad_auth.utilities import bool_from_env, expand_doc
from itsdangerous import URLSafeSerializer
from pkg_resources import parse_version, resource_filename
from pydantic import BaseSettings, DirectoryPath, Field, SecretStr, validator

from docserver.auth.providers.upload import UploadBearerConfig
from docserver.db.config import DBConfig
from docserver.permissions.config import PermissionsConfig


logger = logging.getLogger(__name__)


_DEFAULT_LOGO = '<span class="oi oi-book" title="{app_name}" aria-hidden="true"></span>'


@expand_doc
class UploadConfig(BaseSettings):
    """Configuration for uploading documentation.

    Includes where to upload, and how to store upload requests.
    """
    secret: SecretStr = Field(str(uuid.uuid4()), env='DOCSERVER_UPLOAD_SECRET')
    salt: SecretStr = Field(str(uuid.uuid4()), env='DOCSERVER_UPLOAD_SALT')
    docs_dir: DirectoryPath = Field('/data/www/docs', env='DOCSERVER_DOCS_DIR')
    search_index_dir: DirectoryPath = Field('/data/www/search_indices', env='DOCSERVER_SEARCH_INDEX_DIR')
    releases_only: bool = Field(True, env='DOCSERVER_ACCEPT_ALL')
    package_url_slug: str = Field('/packages', env='DOCSERVER_PACKAGE_URL_SLUG')

    class Config:  # noqa D106
        env_file = '.env'

    _validate_releases_only = validator('releases_only', allow_reuse=True)(bool_from_env)

    @validator('search_index_dir', pre=True, always=True, allow_reuse=True)
    def validate_search_index_dir_exists(cls, value):
        if not os.path.exists(value):
            os.makedirs(value, exist_ok=True)
        return value

    @property
    def serializer(self):
        return URLSafeSerializer(self.secret.get_secret_value(), salt=self.salt.get_secret_value())


LoginUIConfig.__fields__['ui_klass'].default = 'docserver.ui.auth_ui:AuthUI'
LoginUIConfig.__fields__['template_file'].default = resource_filename('docserver.ui.templates', 'login.html')
LoginUIConfig.__fields__['user_template_file'].default = resource_filename('docserver.ui.templates', 'user.html')


class AuthConfig(_AuthConfig):

    user_klass: type = Field('docserver.auth.user:User',
                             description=_AuthConfig.__fields__['user_klass'].field_info.description,
                             env=_AuthConfig.__fields__['user_klass'].field_info.extra['env'])

    class Config:  # noqa D106
        env_file = '.env'
        json_encoders = {
            type: lambda v: f'{v.__module__}:{v.__name__}'
        }

    @validator('providers', always=True)
    def _validate_providers_upload(cls, value, values):
        value.append(UploadBearerConfig(_env_file=cls.Config.env_file))
        return value

    @validator('routing', always=True, pre=True, allow_reuse=True)
    def _fastapi_0_2_0(cls, value):
        # We want to use the fastapi_aad v0.2.0 approach
        if parse_version(fastapi_aad_auth_version) < parse_version('0.2.0'):
            value.login_path = None
            value.login_redirect_path = None
        return value


@expand_doc
class AppConfig(BaseSettings):
    """Overall Application Config.

    Contains the application configuration information.
    """

    upload: UploadConfig = Field(None, description='Configuration for uploading documentation')
    db: DBConfig = Field(None, description='Database Configuration')
    permissions: PermissionsConfig = Field(None, description="Permissions configuration")
    app_name: str = Field('Docserver', description='Application name', env='DOCSERVER_APP_NAME')
    auth: AuthConfig = Field(None, description='Authentication Configuration')
    host_name: Optional[str] = Field(None, description='Host name', env='DOCSERVER_HOST_NAME')
    help_dir: Union[None, DirectoryPath] = Field(None, description='Directory containing built help information', env='DOCSERVER_HELP_DIR')
    logo: str = Field(_DEFAULT_LOGO, description='Logo for the application', env='DOCSERVER_LOGO')

    class Config:  # noqa D106
        env_file = '.env'
        json_encoders = {
            type: lambda v: f'{v.__module__}:{v.__name__}'
        }

    @validator('upload', always=True, pre=True, allow_reuse=True)
    def _validate_upload(cls, value):
        if value is None:
            value = UploadConfig(_env_file=cls.Config.env_file)
        return value

    @validator('db', always=True, pre=True, allow_reuse=True)
    def _validate_db(cls, value):
        if value is None:
            value = DBConfig(_env_file=cls.Config.env_file)
        return value

    @validator('permissions', always=True, pre=True, allow_reuse=True)
    def _validate_permissions(cls, value):
        if value is None:
            value = PermissionsConfig(_env_file=cls.Config.env_file)
        return value

    @validator('auth', always=True, pre=True, allow_reuse=True)
    def _validate_auth(cls, value):
        if value is None:
            value = AuthConfig(_env_file=cls.Config.env_file)
        return value

    @validator('auth', always=True, allow_reuse=True)
    def _validate_auth_app_name(cls, value, values):
        app_name = values.get('app_name', cls.__fields__['app_name'].default)
        value.login_ui.app_name = app_name
        return value

    @validator('auth', always=True, allow_reuse=True)
    def _validate_auth_permission_route(cls, value, values):
        permissions = values['permissions']
        default_write_permission = permissions.default_write_permission
        bearer_providers = [u for u in value.providers if isinstance(u, UploadBearerConfig)]
        if bearer_providers:
            bearer_providers[0].default_write_permission = default_write_permission
        return value

    @validator('logo', always=True)
    def _validate_logo(cls, value, values):
        if '{app_name}' in value:
            value = value.format(app_name=values.get('app_name', 'Docserver'))
        return value


config = AppConfig()
