import logging

from docserver.api import schemas
from docserver.db import models as db_models


logger = logging.getLogger(__name__)


def get_available_docs(provided_permissions=None):
    logger.debug('Getting available docs')
    packages = db_models.Package.read(limit=None, params={})
    # Filter on read permissions
    logger.debug(packages)
    filtered_packages = []
    for package in packages:
        logger.debug(f'{package}, {package.permissions}, {provided_permissions}')
        if package.is_authorised(provided_permissions, 'read'):  # This will return true if auth is disabled
            filtered_packages.append(package)
    for package in filtered_packages:
        if package.description is None:
            package.description = ''
    results = sorted(filtered_packages, key=lambda x: x.name)
    logger.debug(f'Available docs {results}')
    return results


def get_versions(package: schemas.Package, provided_permissions=None):
    db_package = db_models.Package.read_unique(package=package)
    if not db_package.is_authorised(provided_permissions, 'read'):
        raise PermissionError('Missing read permission for package')
    return ['latest'] + db_package.sorted_versions
