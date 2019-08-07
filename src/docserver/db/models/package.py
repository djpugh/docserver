from typing import List, Union

from pkg_resources import parse_version
from sqlalchemy import Column, Integer, String, ForeignKey, or_
from sqlalchemy.orm import relationship, Session

from docserver.app import schemas
from docserver.db.models.base import Model
from docserver.db.models.permission import PermissionCollection
from docserver.db.models.tag import Tag, association_table

# TODO fix tag updating (by id not by obj) - try except somewhere in this


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
    # Permission mappings
    permission_collection_id = Column(Integer, ForeignKey('permissioncollection.id'))

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
                db_tags.append(Tag.get_or_create(db, {'name': tag}))
        return db_tags

    @classmethod
    def create_permissions(cls, db: Session, package: schemas.Package):
        permission_collection = PermissionCollection.get_or_create(db, package.permissions.dict())
        return permission_collection

    @classmethod
    def create(cls, db: Session, params: schemas.Package):
        # Check the permissions here on the Package object
        params_dict = cls.get_write_params_dict(db, params)
        cls.logger.debug(f'Creating Package from {params_dict}')
        obj = super(Package, cls).create(db, params=params_dict)
        cls.logger.debug(f'Created {obj} with {obj.permissions}')
        return obj

    @classmethod
    def get_read_params_dict(cls, db, params):
        if isinstance(params, schemas.Package):
            params.tags = cls.create_tags(db, params)
            params_dict = params.dict()
        elif params:
            params_dict = params.copy()
        else:
            params_dict = dict()
        params_dict.pop('tags', None)
        params_dict.pop('permissions', None)
        return params_dict

    @classmethod
    def get_write_params_dict(cls, db, params):
        if isinstance(params, schemas.Package):
            params_dict = params.dict()
        else:
            params_dict = params.copy()
        params_dict['tags'] = cls.create_tags(db, params)
        params_dict['permissions'] = cls.create_permissions(db, params)
        params_dict.pop('version', None)
        return params_dict

    @classmethod
    def read(cls, db: Session, params: Union[schemas.Package, dict], *args, **kwargs):
        return super(Package, cls).read(db, params=cls.get_read_params_dict(db, params), *args, **kwargs)

    @classmethod
    def read_unique(cls, db: Session, params: Union[schemas.Package, dict],  *args, **kwargs):
        return super(Package, cls).read_unique(db, params=cls.get_read_params_dict(db, params), *args, **kwargs)

    def update(self, db: Session, params: schemas.Package, **kwargs):
        params_dict = self.__class__.get_write_params_dict(db, params)
        return super(Package, self).update(db, params_dict, **kwargs)

    @property
    def html_tags(self):
        return '\n'.join([f'<a href=/search?q=tags:{u.name}><span class="badge badge-info">{u.name}</span></a>' for u in self.tags])

    @classmethod
    def _update_query_with_permissions_check(cls, query, provided_permissions: dict = None, check_scopes: Union[List, str] = 'read'):
        if not isinstance(check_scopes, (list, tuple)):
            check_scopes = [check_scopes]
        or_args = []
        for scope in check_scopes:
            attr = f'{scope}_permission'
            if hasattr(cls, attr):
                or_args.append(getattr(cls, attr).scope.in_(provided_permissions[scope]))
        if or_args:
            cls.logger.debug(f'Or args for filter {or_args}')
            return query.filter(or_(*or_args))
        else:
            return query

    def is_authorised(self, operation, provided_permissions=None):
        return self.permissions.check(operation, provided_permissions.get(operation, []))

    @classmethod
    def update_or_create(cls, db: Session, params: Union[dict, schemas.BaseModel], **kwargs):
        cls.logger.info(f'Update or create object {cls.__name__}')
        provided_permissions = kwargs.pop('provided_permissions', None)
        result = cls.read_unique(db, params=cls._get_unique_params(params.dict()))
        if result:
            if not result.is_authorised('write', provided_permissions=provided_permissions):
                raise PermissionError('Unauthorised')
            result.update(db, params, **kwargs)
            cls.logger.debug(f'{cls.__name__} found with {params}')
        else:
            cls.logger.debug(f'{cls.__name__} not found with {params}')
            for key, value in kwargs.items():
                setattr(params, key, value)
            result = cls.create(db, params)
        return result

    @property
    def search_index(self):
        search_index = {}
        for version in self.versions:
            search_index.update(version.search_index)
        return search_index
