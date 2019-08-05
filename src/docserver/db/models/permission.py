import fnmatch
import logging

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from docserver.auth.permissions import DEFAULTS, OPERATIONS
from docserver.db.models.base import Model

logger = logging.getLogger(__name__)


class Permission(Model):
    id = Column(Integer, primary_key=True)
    operation = Column(String(200), unique=False)
    scope = Column(String(200), unique=False)

    def __repr__(self):
        return f'{self.scope}/{self.operation}'

    def check(self, provided_scopes):
        is_more_powerful_scope = any([fnmatch.fnmatch(self.scope, u) for u in provided_scopes])
        return self.scope in provided_scopes or is_more_powerful_scope


class PermissionCollection(Model):

    id = Column(Integer, primary_key=True)
    packages = relationship("Package", backref="permissions")

    def check(self, operation, provided_scopes):
        return getattr(self, f'{operation}_permission').check(provided_scopes)

    @classmethod
    def read(cls, db, skip=0, limit=100, params=None, **kwargs):
        # need to get the permission objects here
        mapped = cls.get_mapped_permissions(db, params)
        logger.debug(f'Reading permission collection with {mapped}')
        return super().read(db, skip, limit, mapped, **kwargs)

    @classmethod
    def read_unique(cls, db, params=None, **kwargs):
        # need to get the permission objects here
        mapped = cls.get_mapped_permissions(db, params)
        logger.debug(f'Reading unique permission collection with {mapped}')
        return super().read_unique(db, mapped, **kwargs)

    @classmethod
    def create(cls, db, params: dict, **kwargs):
        mapped = cls.get_mapped_permissions(db, params)
        logger.debug(f'Creating permission collection with {mapped}')
        return super().create(db, params=mapped, **kwargs)

    @classmethod
    def get_mapped_permissions(cls, db, params):
        mapped = {}
        if params:
            for op in OPERATIONS:
                scope = params.get(f'{op}_permission', DEFAULTS[op]).split('/')[0]
                permission = Permission.get_or_create(db, dict(operation=op, scope=scope))
                mapped[f'{op}_permission_id'] = permission.id
        return mapped

    def __repr__(self):
        return f'PermissionCollection<{[getattr(self, f"{op}_permission") for op in OPERATIONS]}>'


for op in OPERATIONS:
    setattr(PermissionCollection, f'{op}_permission_id', Column(Integer, ForeignKey('permission.id')))
    setattr(PermissionCollection, f'{op}_permission', relationship('Permission', foreign_keys=[getattr(PermissionCollection, f'{op}_permission_id')]))
