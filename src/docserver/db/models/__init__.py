from docserver.db.models.base import Model
from docserver.db.models.permission import Permission, PermissionCollection  # noqa F401
from docserver.db.models.tag import Tag  # noqa F401
from docserver.db.models.package import Package  # noqa F401
from docserver.db.models.documentation_version import DocumentationVersion  # noqa F401
from docserver.db.models.user import User  # noqa F401


def create_all(config):
    Model.metadata.create_all(bind=config.db.engine)
    Permission.get_or_create(params=dict(operation='read', scope=config.permissions.default_write_permission))
    Permission.get_or_create(params=dict(operation='write', scope=config.permissions.default_read_permission))
    Permission.get_or_create(params=dict(operation='delete', scope=config.permissions.default_delete_permission))
