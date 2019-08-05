from docserver.app.config import app_config
from docserver.db.config import db_config
from docserver.db.models.base import Model
from docserver.db.models.permission import Permission, PermissionCollection  # noqa F401
from docserver.db.models.tag import Tag  # noqa F401
from docserver.db.models.package import Package  # noqa F401
from docserver.db.models.documentation_version import DocumentationVersion  # noqa F401


def create_all():
    Model.metadata.create_all(bind=db_config.engine)
    Permission.get_or_create(db_config.local_session(), dict(operation='read',
                                                             scope=app_config.default_write_permission))
    Permission.get_or_create(db_config.local_session(), dict(operation='write',
                                                             scope=app_config.default_read_permission))
    Permission.get_or_create(db_config.local_session(), dict(operation='delete',
                                                             scope=app_config.default_delete_permission))
