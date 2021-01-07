import json
import os

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import Session

from docserver.api import schemas
from docserver.config import config
from docserver.db.models.base import Model
from docserver.db.models.package import Package
from docserver.search.index import build_index, save_index
from docserver.storage.filesystem import save_docs


class DocumentationVersion(Model):
    id = Column(Integer, primary_key=True)
    url = Column(String(200), unique=True, nullable=False)
    version = Column(String(20), nullable=False)
    package = Column(Integer, ForeignKey('package.id', ondelete="CASCADE"))

    @classmethod
    def create(cls, package: schemas.PackageDocumentationVersion, params: dict, zipfile: str, db_package: Package, db: Session = None):
        # Need to have write permissions for the package
        if db is None:
            db = config.db.local_session()
        save_docs(package, zipfile)
        save_index(package, build_index(package))
        db_documentation_version = super(DocumentationVersion, cls).create(params, db=db)
        db_documentation_version.update_latest(db_package, package)
        return db_documentation_version

    @classmethod
    def update_or_create(cls, package: schemas.PackageDocumentationVersion, zipfile: str, db_package, db: Session = None, **kwargs):
        if db is None:
            db = config.db.local_session()
        provided_permissions = kwargs.pop('provided_permissions', None)
        url = f'{config.upload.package_url_slug}/{package.name.replace(" ", "-")}/{package.version}'
        params = dict(version=package.version,
                      package=db_package.id,
                      url=url)
        cls.logger.debug(f'Creating version {params} for package {db_package}')
        result = cls.read_unique(db=db, params=params)
        if result:
            if not db_package.is_authorised(provided_permissions, 'write'):
                raise PermissionError('Unauthorised')
            cls.logger.debug(f'Found existing version for package {db_package}')
            save_docs(package, zipfile)
            save_index(package, build_index(package))
            cls.logger.debug('Updating docs file')
        else:
            cls.logger.debug(f'Creating new version for package {db_package}')
            result = cls.create(package, params, zipfile, db_package, db=db)
        return result

    def update_latest(self, db_package: Package, package: schemas.Package):
        latest = os.path.join(package.get_dir(), 'latest')
        if db_package.latest_version == self.version:
            # This is the latest version so update/create the symlink
            if os.path.exists(latest):
                os.remove(latest)
            os.symlink(os.path.join(package.get_dir(), package.version), latest, target_is_directory=True)

    def get_index_filename_from_url(self):
        name, version = self.url.split('/')[-2:]
        return os.path.join(config.upload.search_index_dir, f'{name}-{version}.json')

    @property
    def search_index(self):
        index_filename = self.get_index_filename_from_url()
        if os.path.exists(index_filename):
            with open(index_filename) as f:
                return json.load(f)
