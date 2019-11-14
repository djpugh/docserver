import fnmatch
import logging
import os
from typing import List

from pkg_resources import parse_version
from pkg_resources.extern.packaging.version import LegacyVersion
from pydantic import BaseModel, UrlStr, ValidationError, validator
from werkzeug.utils import secure_filename

from docserver.config import config


logger = logging.getLogger(__name__)


class Version(BaseModel):
    version: str = None

    class Config:
        orm_mode = True


class PermissionCollection(BaseModel):
    read_permission: str = config.permissions.default_read_permission
    write_permission: str = config.permissions.default_write_permission
    delete_permission: str = config.permissions.default_delete_permission

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

    @validator('version', always=True, pre=True)
    def validate_semantic_version(cls, version):
        logger.debug(f'Provided version {version}')
        parsed_version = parse_version(version)
        if isinstance(parsed_version, LegacyVersion):
            raise ValueError('Expect semantic version string (Major.Minor.Patch)')
        return str(parsed_version)

    @validator('version')
    def validate_local_version(cls, version):
        logger.debug(f'Provided version {version}')
        parsed_version = parse_version(version)
        if config.upload.releases_only and parsed_version.local is not None:
            raise ValueError('Parsed version {parsed_version} is not a clean semantic version')
        return str(parsed_version)

    def get_path(self):
        return os.path.join(secure_filename(self.name),
                            secure_filename(self.version))

    def get_dir(self):
        return os.path.join(config.upload.docs_dir, secure_filename(self.name))

    def serialize(self):
        params = self.dict()
        return config.upload.serializer.dumps(params)

    @classmethod
    def from_serialized(cls, upload_id):
        params = config.upload.serializer.loads(upload_id)
        logger.debug(f'Loading package from {params}')
        x = cls(**params)
        logger.debug(f'Loaded package {x} from {params}')
        return x

    def __repr__(self):
        return f'CreatePackage ({self.dict()})'

    def check_permissions(self, operation, provided_permissions: list):
        # Handle this through API
        self.permissions.check(operation, provided_permissions)


class ResponsePackage(Package):
    versions: List[Version] = None

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class PermissionManagement(BaseModel):
    username: str
    permission: str


class UserResponse(BaseModel):
    name: str
    email: str
    username: str
    roles: List[str] = []
    groups: List[str] = []
    permissions: List[str] = []

    class Config:
        orm_mode = True
