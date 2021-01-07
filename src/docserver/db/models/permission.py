import fnmatch
import logging

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Session

from docserver.config import config
from docserver.db.models.base import Model
from docserver.permissions import DEFAULTS, OPERATIONS

logger = logging.getLogger(__name__)


class Permission(Model):
    id = Column(Integer, primary_key=True)
    operation = Column(String(200), unique=False)
    scope = Column(String(200), unique=False)

    def __repr__(self):
        return f'{self.scope}/{self.operation}'

    def check(self, provided_permissions):
        provided_scopes = [u.split(f'/{self.operation}')[0] for u in provided_permissions if u.endswith(f'/{self.operation}')]
        logger.debug(f'Provided scopes {provided_scopes}')
        is_more_powerful_scope = any([fnmatch.fnmatch(self.scope, u) for u in provided_scopes])
        return (not config.auth.enabled) or (self.scope in provided_scopes or is_more_powerful_scope)


class PermissionCollection(Model):

    id = Column(Integer, primary_key=True)

    def check(self, operation, provided_permissions):
        if provided_permissions is None:
            provided_permissions = []
        return getattr(self, f'{operation}_permission').check(provided_permissions)

    @classmethod
    def read(cls, db: Session = None, skip=0, limit=100, params=None, **kwargs):
        if db is None:
            db = config.db.local_session()
        # need to get the permission objects here
        mapped = cls.get_mapped_permissions(params, db=db)
        logger.debug(f'Reading permission collection with {mapped}')
        return super().read(skip, limit, params=mapped, db=db, **kwargs)

    @classmethod
    def read_unique(cls, params=None, db: Session = None, **kwargs):
        if db is None:
            db = config.db.local_session()
        # need to get the permission objects here
        mapped = cls.get_mapped_permissions(db=db, params=params)
        logger.debug(f'Reading unique permission collection with {mapped}')
        return super().read_unique(params=mapped, db=db, **kwargs)

    @classmethod
    def create(cls, params: dict, db: Session = None, **kwargs):
        if db is None:
            db = config.db.local_session()
        mapped = cls.get_mapped_permissions(params=params, db=db)
        logger.debug(f'Creating permission collection with {mapped}')
        return super().create(db=db, params=mapped, **kwargs)

    @classmethod
    def get_mapped_permissions(cls, params, db: Session = None):
        if db is None:
            db = config.db.local_session()
        mapped = {}
        if params:
            for op in OPERATIONS:
                scope = params.get(f'{op}_permission', DEFAULTS[op]).split('/')[0]
                permission = Permission.get_or_create(dict(operation=op, scope=scope), db=db)
                mapped[f'{op}_permission_id'] = permission.id
        return mapped

    def __repr__(self):
        return f'PermissionCollection<{[getattr(self, f"{op}_permission") for op in OPERATIONS]}>'


for op in OPERATIONS:
    setattr(PermissionCollection, f'{op}_permission_id', Column(Integer, ForeignKey('permission.id')))
    setattr(PermissionCollection, f'{op}_permission', relationship('Permission',
                                                                   foreign_keys=[getattr(PermissionCollection,
                                                                                         f'{op}_permission_id')]))
