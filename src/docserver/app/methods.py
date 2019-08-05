import logging
import os
import shutil
from tempfile import TemporaryDirectory
import uuid

from docserver.app.config import app_config
from docserver.app import schemas
from docserver.auth.permissions.compare import get_permissions
from docserver.db.config import db_config
from docserver.db.models import Package, DocumentationVersion, Permission


HTML_LATEST_REDIRECT = """
<!DOCTYPE HTML>

<meta charset="UTF-8">
<meta http-equiv="refresh" content="1; url=latest/">

<script>
  window.location.href = "latest/"
</script>
<title>Page Redirection</title>
If you are not redirected automatically, here is the <a href='latest/'>latest documentation</a>
"""

logger = logging.getLogger(__name__)


class ApplicationMethods:

    @staticmethod
    @get_permissions
    def get_available_docs(provided_permissions=None):
        logger.debug(f'Getting available docs')
        packages = Package.read(db=db_config.local_session(), limit=None, params={})
        # Filter on read permissions
        logger.debug(packages)
        filtered_packages = []
        for package in packages:
            logger.debug(f'{package}, {package.permissions}')
            if package.is_authorised('read', provided_permissions):
                filtered_packages.append(package)
        for package in filtered_packages:
            if package.description is None:
                package.description = ''
        results = sorted(filtered_packages, key=lambda x: x.name)
        logger.debug(f'Available docs {results}')
        return results

    @staticmethod
    @get_permissions
    def get_versions(package: schemas.Package, provided_permissions=None):
        db_package = Package.read_unique(db_config.local_session(), package=package)
        if not db_package.is_authorised('read', provided_permissions):
            raise PermissionError('Missing read permission for package')
        return ['latest'] + db_package.sorted_versions

    @staticmethod
    @get_permissions
    def register_package(package: schemas.CreatePackage, provided_permissions=None):
        logger.debug(f'Registering {package}')
        # Check we have write permissions on the package
        try:
            package.check_permissions('write', provided_permissions)
            Package.update_or_create(db_config.local_session(), package, provided_permissions=provided_permissions)
        except PermissionError as e:
            logger.exception('Write permission error')
            raise e

    @get_permissions
    def delete_package(self, package: schemas.Package, provided_permissions=None):
        db = db_config.local_session()
        packages = Package.read(db, package)
        for package in packages:
            if package.is_authorised('delete', provided_permissions):
                db.delete(package)

    @get_permissions
    def save_documentation(self, documentation, package: schemas.CreatePackage, provided_permissions=None):
        result = None
        logger.debug(f'Saving docs for {package}')
        try:
            db = db_config.local_session()
            global_write_permission = Permission.read_unique(db, dict(scope=app_config.default_write_permission,
                                                                      operation='write'))
            if not global_write_permission.check(provided_permissions['write']):
                raise PermissionError
            with TemporaryDirectory() as td:
                filename = os.path.join(td, f'{uuid.uuid4()}.zip')
                with open(filename, 'wb') as dest:
                    shutil.copyfileobj(documentation.file, dest)
                    dest.close()
                    db_package = Package.read_unique(db, package)
                    if not db_package:
                        raise ValueError('No package found')
                    logger.debug(f'Checking permissions for {db_package}')
                    if not db_package.is_authorised('write', provided_permissions):
                        raise PermissionError
                    logger.debug(f'Creating version information for {db_package}')
                    document_version = DocumentationVersion.get_or_create(db, package, filename, db_package)
                    result = document_version.url
                    logger.debug(f'Updating latest docs for {package}')
                    self._check_redirect(package)
        except PermissionError as e:
            logger.exception('Write permission error')
            raise e
        return result

    @staticmethod
    def _check_redirect(package: schemas.Package):
        index = os.path.join(package.get_dir(), 'index.html')
        if not os.path.exists(index):
            logger.debug(f'Creating redirect for {package}')
            with open(index, 'w') as f:
                f.write(HTML_LATEST_REDIRECT)
                f.close()

    @staticmethod
    def make_path(path):
        required_dir = os.path.join(app_config.docs_dir, path)
        if not os.path.exists(required_dir):
            os.makedirs(required_dir)
        return required_dir
