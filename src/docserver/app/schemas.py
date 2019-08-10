import fnmatch
import logging
import os
from typing import List

from itsdangerous import URLSafeSerializer
from pkg_resources import parse_version
from pkg_resources.extern.packaging.version import LegacyVersion
from pydantic import BaseModel, validator, ValidationError, UrlStr
from werkzeug.utils import secure_filename

from docserver.app.config import app_config


s = URLSafeSerializer(app_config.key, salt=app_config.salt)
logger = logging.getLogger(__name__)


class Version(BaseModel):
    version: str = None

    class Config:
        orm_mode = True


class PermissionCollection(BaseModel):
    read_permission: str = app_config.default_read_permission
    write_permission: str = app_config.default_write_permission
    delete_permission: str = app_config.default_delete_permission

    class Config:
        orm_mode = True

    def check(self, operation, provided_scopes):
        scope = getattr(self, f'{operation}_permission').split('/')[0]
        is_more_powerful_scope = any([fnmatch.fnmatch(scope, u) for u in provided_scopes])
        return scope in provided_scopes or is_more_powerful_scope

    @validator('read_permission', 'write_permission', 'delete_permission', pre=True, always=True)
    def validate_permissions(cls, permission):
        if not isinstance(permission, str):
            return f'{permission.scope}/{permission.operation}'
        else:
            return permission


class Package(BaseModel):
    name: str
    repository: UrlStr
    tags: List[str]
    description: str = None
    permissions: PermissionCollection = PermissionCollection()

    @validator('tags', pre=True, always=True)
    def validate_tags(cls, tag):
        if not isinstance(tag, str):
            return str(tag.name)
        else:
            return tag


class CreatePackage(Package):
    version: str = None

    class Config:
        orm_mode = True

    @validator('version')
    def validate_semantic_version(cls, version):
        print(version)
        parsed_version = parse_version(version)
        if isinstance(parsed_version, LegacyVersion):
            raise ValidationError('Expect semantic version string (Major.Minor.Patch)')
        return str(parsed_version)

    @validator('version')
    def validate_local_version(cls, version):
        print(version)
        parsed_version = parse_version(version)
        if app_config.releases_only and parsed_version.local is not None:
            raise ValidationError('Parsed version {parsed_version} is not a clean semantic version')
        return str(parsed_version)

    def get_path(self):
        return os.path.join(secure_filename(self.name),
                            secure_filename(self.version))

    def get_dir(self):
        return os.path.join(app_config.docs_dir, secure_filename(self.name))

    def serialize(self):
        params = self.dict()
        return s.dumps(params)

    @classmethod
    def from_serialized(cls, upload_id):
        params = s.loads(upload_id)
        logger.debug(f'Loading package from {params}')
        x = cls(**params)
        logger.debug(f'Loaded package {x} from {params}')
        return x

    def __repr__(self):
        return f'CreatePackage ({self.dict()})'

    def check_permissions(self, operation, provided_permissions: dict):
        self.permissions.check(operation, provided_permissions.get(operation, []))


class ResponsePackage(Package):
    versions: List[Version] = None

    class Config:
        orm_mode = True
