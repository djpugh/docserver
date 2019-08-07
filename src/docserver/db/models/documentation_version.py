import json
import os
from zipfile import ZipFile

from bs4 import BeautifulSoup
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
        cls.save_docs(package, zipfile)
        db_documentation_version = super(DocumentationVersion, cls).create(db, params)
        db_documentation_version.update_latest(db_package, package)
        return db_documentation_version

    @classmethod
    def save_docs(cls, package: schemas.CreatePackage, zipfile: str, ):
        # Need to have write permissions for the package
        path = make_path(package.get_path())
        zf = ZipFile(zipfile)
        for subfile in zf.namelist():
            zf.extract(subfile, path)
        zf.close()
        cls.save_index(package, cls.build_index(package))

    @classmethod
    def update_or_create(cls, db: Session, package: schemas.CreatePackage, zipfile: str, db_package, **kwargs):
        provided_permissions = kwargs.pop('provided_permissions', None)
        url = f'{app_config.package_url_slug}/{package.name}/{package.version}'
        params = dict(version=package.version,
                      package=db_package.id,
                      url=url)
        cls.logger.debug(f'Creating version {params} for package {db_package}')
        result = cls.read_unique(db, params=params)
        if result:
            if not db_package.is_authorised('write', provided_permissions=provided_permissions):
                raise PermissionError('Unauthorised')
            cls.logger.debug(f'Found existing version for package {db_package}')
            cls.save_docs(package, zipfile)
            cls.logger.debug(f'Updating docs file')
        else:
            cls.logger.debug(f'Creating new version for package {db_package}')
            result = cls.create(db, package, params, zipfile, db_package)
        return result

    def update_latest(self, db_package: Package, package: schemas.Package):
        latest = os.path.join(package.get_dir(), 'latest')
        if db_package.latest_version == self.version:
            # This is the latest version so update/create the symlink
            if os.path.exists(latest):
                os.remove(latest)
            os.symlink(os.path.join(package.get_dir(), package.version), latest, target_is_directory=True)

    @classmethod
    def build_index(cls, package: schemas.CreatePackage):
        url = f'{app_config.package_url_slug}/{package.name}/{package.version}'
        index = {}
        base_dir = os.path.join(package.get_dir(), package.version)
        tags = []
        for tag in package.tags:
            if isinstance(tag, str):
                tags.append(tag)
            else:
                tags.append(tag.name)
        tag_str = ';'.join(tags)
        for (root, _, files) in os.walk(base_dir):
            for filename in files:
                if filename.endswith('.html'):
                    filepath = os.path.join(root, filename)
                    with open(filepath) as f:
                        soup = BeautifulSoup(f.read(), features="html.parser")
                        # Build the link
                        link = f'{url}/{os.path.relpath(filepath, base_dir)}'.replace(os.path.sep, '/')
                        if soup.title:
                            title = soup.title.string
                        else:
                            title = os.path.split(filename)[-1]
                        doc = dict(body=soup.get_text(' '), link=link, title=title)
                        doc['tags'] = tag_str
                        doc['description'] = package.description
                        doc['name'] = package.name
                        doc['repository'] = package.repository
                        doc['root_url'] = url
                        doc['version'] = package.version
                        index[doc['link']] = doc
        return index

    @classmethod
    def get_index_filename(cls, name, version):
        return os.path.join(app_config.search_index_dir, f'{name}-{version}.json')

    def get_index_filename_from_url(self):
        name, version = self.url.split('/')[-2:]
        return os.path.join(app_config.search_index_dir, f'{name}-{version}.json')

    @classmethod
    def save_index(cls, package, index):
        # Save this as a JSON
        if not os.path.exists(app_config.search_index_dir):
            os.makedirs(app_config.search_index_dir, exist_ok=True)
        index_filename = cls.get_index_filename(package.name, package.version)
        with open(index_filename, 'w') as f:
            json.dump(index, f)

    @property
    def search_index(self):
        index_filename = self.get_index_filename_from_url()
        if os.path.exists(index_filename):
            with open(index_filename) as f:
                return json.load(f)


def make_path(path):
    required_dir = os.path.join(app_config.docs_dir, path)
    if not os.path.exists(required_dir):
        os.makedirs(required_dir, exist_ok=True)
    return required_dir
