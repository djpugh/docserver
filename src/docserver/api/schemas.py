from datetime import datetime
import fnmatch
import logging
import os
from typing import List, Optional

from pkg_resources import parse_version
from pkg_resources.extern.packaging.version import LegacyVersion
from pydantic import AnyUrl, BaseModel, validator
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
        logger.debug(f'Checking if more powerful scope than {scope} in {provided_scopes}')
        # We will drop 'authenticated' and 'admin'
        is_more_powerful_scope = any([fnmatch.fnmatch(scope, u.split('/')[0]) for u in provided_scopes if u.endswith(operation) and '/' in u])
        logger.debug(f'More powerful scope {is_more_powerful_scope}')
        logger.debug(f'Checking {scope} in {provided_scopes}')
        return f'{scope}/{operation}' in provided_scopes or is_more_powerful_scope

    @validator('read_permission', 'write_permission', 'delete_permission', pre=True, always=True)
    def validate_permissions(cls, permission):
        if not isinstance(permission, str):
            return f'{permission.scope}/{permission.operation}'
        else:
            return permission

class BasePackage(BaseModel):
    name: str

    @property
    def route_name(self):
        return self.name.replace(' ', '-')

    def get_dir(self):
        return os.path.join(config.upload.docs_dir, secure_filename(self.route_name))


class Package(BasePackage):
    repository: AnyUrl
    tags: List[str]
    description: str = None
    permissions: PermissionCollection = PermissionCollection()

    @validator('tags', pre=True, always=True, each_item=True)
    def validate_tags(cls, tag):
        logger.debug(tag)
        if not isinstance(tag, (str, list)):
            return str(tag.name)
        else:
            return tag

    def check_permissions(self, provided_permissions: list, *operations):
        # Handle this through API
        logger.debug(f'Checking {provided_permissions} for {operations}')
        result = False
        for operation in operations:
            result |= self.permissions.check(operation, provided_permissions)
        return result


class BasePackageVersion(BasePackage):
    version: str = None

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
        return os.path.join(self.get_dir(),
                            secure_filename(self.version))


class PackageDocumentationVersion(BasePackageVersion, Package):

    class Config:
        orm_mode = True

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
        return f'PackageDocumentationVersion ({self.dict()})'


class ResponsePackage(Package):
    versions: List[Version] = None

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None

    @validator('expires_at', pre=True)
    def _validate_expires_at(cls, value):
        print(value)
        return value


class PermissionManagement(BaseModel):
    username: str
    permission: str


class UserResponse(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    roles: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    permissions: List[str] = []

    class Config:
        orm_mode = True
