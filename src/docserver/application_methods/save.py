import logging
import os
import shutil
from tempfile import TemporaryDirectory
import uuid

from docserver.api import schemas
from docserver.application_methods import redirect
from docserver.config import config
from docserver.db import models as db_models

logger = logging.getLogger(__name__)


def save_documentation(documentation, package: schemas.CreatePackage, provided_permissions=None):
    result = None
    logger.debug(f'Saving docs for {package}')
    try:
        db = config.db.local_session()
        global_write_permission = db_models.Permission.read_unique(db, dict(scope=config.permissions.default_write_permission,
                                                                            operation='write'))
        if not global_write_permission.check(provided_permissions):
            raise PermissionError
        with TemporaryDirectory() as td:
            filename = os.path.join(td, f'{uuid.uuid4()}.zip')
            with open(filename, 'wb') as dest:
                shutil.copyfileobj(documentation.file, dest)
                dest.close()
                db_package = db_models.Package.read_unique(db=db, params=package)
                if not db_package:
                    raise ValueError('No package found')
                logger.debug(f'Checking permissions for {db_package}')
                if not db_package.is_authorised('write', provided_permissions):
                    raise PermissionError
                logger.debug(f'Creating version information for {db_package}')
                document_version = db_models.DocumentationVersion.update_or_create(db=db, package=package,
                                                                                   zipfile=filename,
                                                                                   db_package=db_package,
                                                                                   provided_permissions=provided_permissions)
                result = document_version.url
                logger.debug(f'Updating latest docs for {package}')
                redirect.check_redirect(package)
    except PermissionError as e:
        logger.exception('Write permission error')
        raise e
    return result
