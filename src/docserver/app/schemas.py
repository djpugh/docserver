import os
from typing import List

from pkg_resources import parse_version
from pkg_resources.extern.packaging.version import LegacyVersion
from pydantic import BaseModel, validator, ValidationError
from werkzeug.utils import secure_filename

from docserver.app.config import app_config


class Tag(BaseModel):
    name: str

    class Config:
        orm_mode = True


class Version(BaseModel):
    version: str = None

    class Config:
        orm_mode = True


class Package(BaseModel):
    name: str
    repository: str
    tags: List[Tag]
    description: str = None


class CreatePackage(Package):
    version: str = None

    class Config:
        orm_mode = True

    @classmethod
    @validator('version')
    def validate_semantic_version(cls, version):
        parsed_version = parse_version(version)
        if isinstance(parsed_version, LegacyVersion):
            raise ValidationError('Expect semantic version string (Major.Minor.Patch)')

    @classmethod
    @validator('version')
    def validate_local_version(cls, version):
        parsed_version = parse_version(version)
        if app_config.releases_only and parsed_version.local is not None:
            raise ValidationError('Parsed version {parsed_version} is not a clean semantic version')

    def get_path(self):
        return os.path.join(secure_filename(self.name),
                            secure_filename(self.version))

    def get_dir(self):
        return os.path.join(app_config.docs_dir, secure_filename(self.name))


class ResponsePackage(Package):
    versions: List[Version] = None

    class Config:
        orm_mode = True
