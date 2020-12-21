from typing import List

from pydantic import BaseSettings, Field, validator

from docserver.permissions import DEFAULTS


class PermissionsConfig(BaseSettings):
    default_write_permission: str = Field(DEFAULTS['write'], env='DOCSERVER_DEFAULT_WRITE_SCOPE')
    default_read_permission: str = Field(DEFAULTS['read'], env='DOCSERVER_DEFAULT_READ_SCOPE')
    default_delete_permission: str = Field(DEFAULTS['delete'], env='DOCSERVER_DEFAULT_DELETE_SCOPE')
    default_admin_permission: str = Field(DEFAULTS['admin'], env='DOCSERVER_DEFAULT_ADMIN_SCOPE')
    admin_users: List[str] = Field(None, env='DOCSERVER_ADMIN_USERS')

    class Config:  # noqa D106
        env_file = '.env'

    @validator('admin_users', pre=True, always=True)
    def _validate_admin_users(cls, value):
        if value is None:
            value = []
        return value
