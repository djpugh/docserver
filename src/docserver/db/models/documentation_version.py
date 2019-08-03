import os
from zipfile import ZipFile

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Session

from docserver.app import schemas
from docserver.app.config import app_config
from docserver.db.models.base import Model
from docserver.db.models.package import Package


class DocumentationVersion(Model):
    id = Column(Integer, primary_key=True)
    url = Column(String(200), unique=True, nullable=False)
    version = Column(String(20), nullable=False)
    package = Column(Integer, ForeignKey('package.id'))

    @classmethod
    def create(cls, db: Session, package: schemas.CreatePackage, params: dict, zipfile: str, db_package: Package):
        # Need to have write permissions for the package
        path = make_path(package.get_path())
        zf = ZipFile(zipfile)
        for subfile in zf.namelist():
            zf.extract(subfile, path)
        zf.close()
        db_documentation_version = super(DocumentationVersion, cls).create(db, params)
        db_documentation_version.update_latest(db_package, package)
        return db_documentation_version

    @classmethod
    def get_or_create(cls, db: Session, package: schemas.CreatePackage, zipfile: str, db_package):
        url = f'{app_config.package_url_slug}/{package.name}/{package.version}'
        params = dict(version=package.version,
                      package=db_package.id,
                      url=url)
        cls.logger.debug(f'Creating version {params} for package {db_package}')
        result = cls.read_unique(db, params=params)
        if result:
            cls.logger.debug(f'Found existing version for package {db_package}')
            return result
        else:
            cls.logger.debug(f'Creating new version for package {db_package}')
            return cls.create(db, package, params, zipfile, db_package)

    def update_latest(self, db_package: Package, package: schemas.Package):
        latest = os.path.join(package.get_dir(), 'latest')
        if db_package.latest_version == self.version:
            # This is the latest version so update/create the symlink
            if os.path.exists(latest):
                os.remove(latest)
            os.symlink(os.path.join(package.get_dir(), package.version), latest, target_is_directory=True)


def make_path(path):
    required_dir = os.path.join(app_config.docs_dir, path)
    if not os.path.exists(required_dir):
        os.makedirs(required_dir)
    return required_dir
