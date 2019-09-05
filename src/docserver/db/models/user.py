from sqlalchemy import Column, String, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship, Session

from docserver.auth.providers.basic import BasicAuthProvider
from docserver.config import config
from docserver.db.models.base import Model
from docserver.db.models.permission import Permission
from docserver.permissions import OPERATIONS

association_table = Table('user_association', Model.metadata,
                          Column('user_id', Integer, ForeignKey('user.id')),
                          Column('permission_id', Integer, ForeignKey('permission.id')))


class User(Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(300), unique=True, )
    permissions = relationship(
        "Permission",
        secondary=association_table)

    def add_permission(self, permission, db: Session = None):
        if db is None:
            db = config.db.local_session()
        scope, op = permission.split('/')
        if op not in OPERATIONS:
            raise ValueError(f'Incorrect operation {op} - not in {OPERATIONS}')
        permission = Permission.get_or_create(dict(operation=op, scope=scope), db=db)
        if permission not in self.permissions:
            self.permissions.append(permission)
        db.add(self)
        db.commit()
        db.refresh(self)

    def remove_permission(self, permission, db: Session = None):
        if db is None:
            db = config.db.local_session()
        scope, op = permission.split('/')
        if op not in OPERATIONS:
            raise ValueError(f'Incorrect operation {op} - not in {OPERATIONS}')
        permission = Permission.read_unique(params=dict(operation=op, scope=scope), db=db)

        if permission and permission in self.permissions:
                self.permissions = [u for u in self.permissions if u.id != permission.id]
        db.add(self)
        db.commit()
        db.refresh(self)


if config.auth.enabled and isinstance(config.auth.provider_object, BasicAuthProvider):
    # This is a User object which handles passwords
    pass
