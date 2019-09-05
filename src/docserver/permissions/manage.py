import logging

from docserver.config import config
from docserver.db import models as db_models


logger = logging.getLogger(__name__)


def add_permission(username: str, permission: str, provided_permissions=None):
    db = config.db.local_session()
    global_admin_permission = db_models.Permission.read_unique(db, dict(scope=config.permissions.default_admin_permission,
                                                                        operation='admin'))
    if not global_admin_permission.check(provided_permissions):
        raise PermissionError
    user = db_models.User.get_or_create(dict(username=username), db=db)
    user.add_permission(permission, db=db)


def remove_permission(username: str, permission: str, provided_permissions=None):
    db = config.db.local_session()
    global_admin_permission = db_models.Permission.read_unique(db, dict(scope=config.permissions.default_admin_permission,
                                                                        operation='admin'))
    if not global_admin_permission.check(provided_permissions):
        raise PermissionError
    user = db_models.User.get_or_create(dict(username=username), db=db)
    user.remove_permission(permission, db=db)
