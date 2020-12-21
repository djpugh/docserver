"""Authentication User object with db handling"""
import logging
from typing import List

from fastapi_aad_auth._base.state import User as _User
from pydantic import BaseModel

from docserver import db
from docserver.auth.abac import get_permissions


logger = logging.getLogger(__name__)


class User(_User):

    @property
    def permissions(self):
        mapped_permissions = get_permissions(self)
        db_user = db.models.User.read_unique(params=dict(username=self.username))
        logger.debug(f'{self.name}: db_user {db_user}')
        if db_user:
            logger.debug(f'User: {self.name}; db permissions: {db_user.permissions}')
            mapped_permissions += [str(u) for u in db_user.permissions if str(u) not in mapped_permissions]
            logger.debug(f'{self.name}: db updated permissions {mapped_permissions}')
        logger.debug(f'{self.name} - checking for admin permissions')
        admin_permissions = []
        for permission in mapped_permissions:
            if permission.endswith('/admin'):
                logger.debug(f'{self.name} - admin ({permission}) - adding read, write, delete permissions')
                admin_permissions += [permission.replace('/admin', '/read'), permission.replace('/admin', '/write'), permission.replace('/admin', '/delete')]
        mapped_permissions += admin_permissions
        logger.debug(f'{self.name}: combined permissions {mapped_permissions}')
        return list(set(mapped_permissions))

# TODO: Check How this works with state/user


class APIUser(BaseModel):

    permissions: List[str] = []
