import logging
import os
import uuid

from itsdangerous import URLSafeSerializer
from pydantic import BaseModel, UrlStr, DirectoryPath, Schema, SecretStr, validator

from docserver.auth.config import AuthConfig
from docserver.db.config import DBConfig
from docserver.permissions.config import PermissionsConfig


logger = logging.getLogger(__name__)


class UploadConfig(BaseModel):
    secret: SecretStr = Schema(SecretStr(os.getenv('DOCSERVER_UPLOAD_SECRET', str(uuid.uuid4()))))
    salt: SecretStr = Schema(SecretStr(os.getenv('DOCSERVER_UPLOAD_SALT', str(uuid.uuid4()))))
    docs_dir: DirectoryPath = Schema(os.getenv('DOCSERVER_DOCS_DIR', '/data/www/docs'))
    search_index_dir: DirectoryPath = Schema(os.getenv('DOCSERVER_SEARCH_INDEX_DIR', '/data/www/search_indices'))
    releases_only: bool = Schema(os.getenv('DOCSERVER_ACCEPT_ALL', '0'))
    package_url_slug: UrlStr = os.getenv('DOCSERVER_PACKAGE_URL_SLUG', '/packages')

    @validator('releases_only', pre=True, always=True)
    def validate_releases_only(cls, value):
        return str(value).lower() in ['1', 'true']

    @validator('search_index_dir', pre=True, always=True)
    def validate_search_index_dir_exists(cls, value):
        if not os.path.exists(value):
            os.makedirs(value, exist_ok=True)
        return value

    @property
    def serializer(self):
        return URLSafeSerializer(self.secret.get_secret_value(), salt=self.salt.get_secret_value())


class AppConfig(BaseModel):

    upload: UploadConfig = Schema(UploadConfig())
    auth: AuthConfig = Schema(AuthConfig())
    db: DBConfig = Schema(DBConfig())
    permissions: PermissionsConfig = Schema(PermissionsConfig())
    app_name: str = Schema(os.environ.get('DOCSERVER_SERVER_NAME', 'Docserver'))
    host_name: str = Schema(os.environ.get('DOCSERVER_HOST_NAME', None))


config = AppConfig()
