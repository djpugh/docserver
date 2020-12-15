import logging

from docserver.api import schemas
from docserver.db import models as db_models


logger = logging.getLogger(__name__)


def register_package(package: schemas.CreatePackage, provided_permissions=None):
    logger.debug(f'Registering {package}')
    # Check we have write permissions on the package
    if package.check_permissions(provided_permissions, 'write'):
        db_models.Package.update_or_create(package, provided_permissions=provided_permissions)
    else:
        logger.exception('Write permission error')
        raise PermissionError
