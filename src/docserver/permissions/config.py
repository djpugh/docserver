import os

from pydantic import BaseModel, Schema

from docserver.permissions import DEFAULTS


class PermissionsConfig(BaseModel):
    default_write_permission: str = Schema(os.getenv('DOCSERVER_DEFAULT_WRITE_SCOPE', DEFAULTS['write']))
    default_read_permission: str = Schema(os.getenv('DOCSERVER_DEFAULT_READ_SCOPE', DEFAULTS['read']))
    default_delete_permission: str = Schema(os.getenv('DOCSERVER_DEFAULT_DELETE_SCOPE', DEFAULTS['delete']))
