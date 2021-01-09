import logging

from docserver.api import schemas
from docserver.config import config
from docserver.db import models as db_models


logger = logging.getLogger(__name__)


def delete_package(package: schemas.BasePackage, provided_permissions=None):
    db = config.db.local_session()
    packages = db_models.Package.read(params=package.dict(), db=db)
    for package in packages:
        if package.is_authorised(provided_permissions, 'delete'):
            # TODO: Delete all the versions (and from storage)
            db.delete(package)
            db.commit()


def delete_version(documentation_version: schemas.BasePackageVersion, provided_permissions=None):
    db = config.db.local_session()
    packages = db_models.Package.read(params=documentation_version.dict(), db=db)
    deleted = []
    for package in packages:
        package_version = package.get_version(documentation_version.version)
        if package_version and package.is_authorised(provided_permissions, 'delete'):
            # TODO: Delete the version (from storage)
            db.delete(package_version)
            db.commit()
            deleted.append(f'{package.name}-{package_version.version}')
        db.refresh(package)
        if not package.versions:
            db.delete(package)
            db.commit()
            deleted.append(f'{package.name}')
    return deleted
