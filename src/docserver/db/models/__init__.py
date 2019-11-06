import logging

from docserver.db.models.base import Model
from docserver.db.models.permission import Permission, PermissionCollection  # noqa F401
from docserver.db.models.tag import Tag  # noqa F401
from docserver.db.models.package import Package  # noqa F401
from docserver.db.models.documentation_version import DocumentationVersion  # noqa F401
from docserver.db.models.user import User  # noqa F401


logger = logging.getLogger('.'.join(__name__.split('.')[:-1]))


def create_all(config):
    logger.info('Creating all DB tables')
    Model.metadata.create_all(bind=config.db.engine)
    db = config.db.local_session()
    logger.info('Creating permissions')
    Permission.get_or_create(db=db, params=dict(operation='read', scope=config.permissions.default_write_permission))
    Permission.get_or_create(db=db, params=dict(operation='write', scope=config.permissions.default_read_permission))
    Permission.get_or_create(db=db, params=dict(operation='delete', scope=config.permissions.default_delete_permission))
    admin = Permission.get_or_create(db=db, params=dict(operation='admin', scope=config.permissions.default_admin_permission))
    logger.debug(admin)
    logger.info('Setting admin users')
    for username in config.permissions.admin_users:
        user = User.get_or_create(params=dict(username=username), db=db)
        user.add_permission(str(admin), db=db)
        logger.debug(user)
    logger.info('DB preparation complete')
