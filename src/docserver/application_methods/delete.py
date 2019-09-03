import logging

from docserver.api import schemas
from docserver.config import config
from docserver.db import models as db_models


logger = logging.getLogger(__name__)


def delete_package(package: schemas.Package, provided_permissions=None):
    db = config.db.local_session()
    packages = db_models.Package.read(db, package)
    for package in packages:
        if package.is_authorised('delete', provided_permissions):
            db.delete(package)
