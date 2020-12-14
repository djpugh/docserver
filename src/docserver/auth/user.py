from fastapi_aad_auth._base.state import User as _User
from pydantic import BaseModel
from typing import List

from docserver.auth.abac import get_permissions
from docserver.db import models as db_models


class User(_User):

    name: str
    email: str
    username: str
    roles: List[str] = []
    groups: List[str] = []

    @property
    def permissions(self):
        mapped_permissions = get_permissions(self)
        db_user = db_models.User.read_unique(params=dict(username=self.username))
        if db_user:
            print(db_user.permissions)
            mapped_permissions += [str(u) for u in db_user.permissions if str(u) not in mapped_permissions]
        return mapped_permissions

class APIUser(BaseModel):
    permissions: List[str] = []
