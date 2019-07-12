import os
from typing import Union
from zipfile import ZipFile

from pkg_resources import parse_version
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql.schema import PrimaryKeyConstraint, UniqueConstraint

from docserver.app import schemas
from docserver.app.config import app_config
from docserver.db.config import db_config


class CustomBase:
    # Generate __tablename__ automatically

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @classmethod
    def create(cls, db: Session, params: dict):
        db_object = cls(**params)
        db.add(db_object)
        db.commit()
        db.refresh(db_object)
        return db_object

    @classmethod
    def read(cls, db: Session, skip: int = 0, limit: int = 100, params: dict = None):
        if params is None:
            compare_params = dict()
        else:
            compare_params = {u.name: params[u.name] for u in cls.__table__.columns if u.name in params.keys()}
        return db.query(cls).filter_by(**compare_params).offset(skip).limit(limit).all()

    @classmethod
    def update(cls, db: Session, params: dict, **kwargs):
        unique_columns = []
        for constraint in cls.__table__.constraints:
            if isinstance(constraint, (UniqueConstraint, PrimaryKeyConstraint)):
                unique_columns += [column.name for column in constraint.columns]
        compare_params = {column: params[column] for column in unique_columns if column in params.keys()}
        db_object = db.query(cls).filter_by(**compare_params).first()
        params.update(kwargs)
        for key, value in params.items():
            setattr(db_object, key, value)
        db.commit()
        db.refresh(db_object)
        return db_object

    @classmethod
    def delete(cls, db: Session, params: dict):
        db_object = db.query(cls).filter_by(**params).first()
        db.commit()
        db.refresh(db_object)
        return db_object

    @classmethod
    def get_or_create(cls, db: Session, params: Union[dict, schemas.BaseModel]):
        result = cls.read(db, params=params)
        if result:
            return result[0]
        else:
            return cls.create(db, params)

    @classmethod
    def update_or_create(cls, db: Session, params: Union[dict, schemas.BaseModel], **kwargs):
        result = cls.read(db, params=params)
        if result:
            return cls.update(db, params=params, **kwargs)
        else:
            for key, value in kwargs.items():
                setattr(params, key, value)
            return cls.create(db, params)


Model = declarative_base(cls=CustomBase)


association_table = Table('association', Model.metadata,
                          Column('tag_id', Integer, ForeignKey('tag.id')),
                          Column('package_id', Integer, ForeignKey('package.id')))


class Tag(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    packages = relationship(
        "Package",
        secondary=association_table,
        back_populates="tags")

    def __repr__(self):
        return self.name

    @classmethod
    def create(cls, db: Session, params: schemas.Tag):
        return super(Tag, cls).create(db, params.dict())

    @classmethod
    def read(cls, db: Session, params: schemas.Tag, *args, **kwargs):
        return super(Tag, cls).read(db, params=params.dict(), *args, **kwargs)

    @classmethod
    def get_or_create(cls, db: Session, params: schemas.Tag):
        return super(Tag, cls).get_or_create(db, params=params)

    @classmethod
    def update(cls, db: Session, params: schemas.Tag, **kwargs):
        return super(Tag, cls).update(db, params.dict(), **kwargs)


class Package(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    tags = relationship(
        "Tag",
        secondary=association_table,
        back_populates="packages")

    versions = relationship("DocumentationVersion")
    repository = Column(String(300), unique=True, nullable=False)
    description = Column(String(800), nullable=True)

    def __repr__(self):
        tags = []
        for tag in self.tags:
            tags.append(tag.name)
        return f'<Package {self.name} ({", ".join(tags)})>'

    @property
    def sorted_versions(self):
        return sorted([u.version for u in self.versions],
                      key=lambda x: parse_version(x), reverse=True)

    @property
    def latest_version(self):
        versions = self.sorted_versions
        if versions:
            return versions[0]
        else:
            return ''

    @staticmethod
    def create_tags(db: Session, package: schemas.Package):
        db_tags = []
        for tag in getattr(package, 'tags', []):
            if isinstance(tag, Tag):
                db_tags.append(tag)
            else:
                db_tags.append(Tag.get_or_create(db, tag))
        return db_tags

    @classmethod
    def create(cls, db: Session, params: schemas.Package):
        params.tags = cls.create_tags(db, params)
        params_dict = params.dict()
        params_dict.pop('version', None)
        return super(Package, cls).create(db, params=params_dict)

    @classmethod
    def read(cls, db: Session, params: schemas.Package, *args, **kwargs):
        if params:
            params.tags = cls.create_tags(db, params)
            params_dict = params.dict()
        else:
            params_dict = dict()
        params_dict.pop('tags', None)
        return super(Package, cls).read(db, params=params_dict, *args, **kwargs)

    @classmethod
    def get_or_create(cls, db: Session, params: schemas.Package):
        return super(Package, cls).get_or_create(db, params=params)

    @classmethod
    def update(cls, db: Session, params: schemas.Package, **kwargs):
        return super(Package, cls).update(db, params.dict(), **kwargs)

    @property
    def html_tags(self):
        return '\n'.join([f'<span class="badge badge-info">{u.name}</span>' for u in self.tags])


class DocumentationVersion(Model):
    id = Column(Integer, primary_key=True)
    url = Column(String(200), unique=True, nullable=False)
    version = Column(String(20), nullable=False)
    package = Column(Integer, ForeignKey('package.id'))

    @classmethod
    def create(cls, db: Session, package: schemas.Package, zipfile: str):
        path = make_path(package.get_path())
        zf = ZipFile(zipfile)
        for subfile in zf.namelist():
            zf.extract(subfile, path)
        zf.close()
        db_package = Package.update_or_create(db, package)
        url = f'{app_config.package_url_slug}/{package.name}/{package.version}'
        db_documentation_version = super(DocumentationVersion, cls).create(db, dict(version=package.version,
                                                                                    package=db_package.id,
                                                                                    url=url))
        db_documentation_version.update_latest(db_package, package)
        return db_documentation_version

    @classmethod
    def get_or_create(cls, db: Session, package: schemas.Package, zipfile: str):
        db_package = Package.get_or_create(db, package)
        url = f'{app_config.package_url_slug}/{package.name}/{package.version}'
        params = dict(version=package.version,
                      package=db_package.id,
                      url=url)
        result = cls.read(db, params=params)
        if result:
            return result[0]
        else:
            return cls.create(db, package, zipfile)

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


def create_all():
    Model.metadata.create_all(bind=db_config.engine)
