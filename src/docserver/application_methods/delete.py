import logging

from docserver.api import schemas
from docserver.config import config
from docserver.db import models as db_models
from docserver.storage import filesystem


logger = logging.getLogger(__name__)


def delete_package(package: schemas.BasePackage, provided_permissions=None):
    db = config.db.local_session()
    packages = db_models.Package.read(params=package.dict(), db=db)
    deleted = []
    for package in packages:
        if package.is_authorised(provided_permissions, 'delete'):
            package.delete(db=db)
            deleted.append(package.name)
    return deleted

def delete_version(documentation_version: schemas.BasePackageVersion, provided_permissions=None):
    db = config.db.local_session()
    packages = db_models.Package.read(params=documentation_version.dict(), db=db)
    deleted = []
    for package in packages:
        package_version = package.get_version(documentation_version.version)
        if package_version and package.is_authorised(provided_permissions, 'delete'):
            # TODO: Delete the version (from storage)
            package_version.delete(db=db)
            deleted.append(f'{package.name}-{package_version.version}')
        db.refresh(package)
        if not package.versions:
            package.delete(db=db)
            deleted.append(package.name)
    return deleted
