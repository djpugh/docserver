import logging
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import EmailStr

from docserver.api import schemas
from docserver.auth.authenticator import AuthenticationState, authenticator
from docserver.permissions import manage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/add')
async def add_permission(body: schemas.PermissionManagement, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """
    Add a permission for a user
    """
    return manage.add_permission(username=body.username, permission=body.permission,
                                 provided_permissions=state.user.permissions)


@router.post('/remove')
async def remove_permission(body: schemas.PermissionManagement, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """
    Remove a permission from a user
    """
    return manage.remove_permission(username=body.username, permission=body.permission,
                                    provided_permissions=state.user.permissions)


@router.post('/list', response_model=List[str])
async def list_permission(username: Optional[EmailStr] = None, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """
    List permissions for a user (defaults to the token user)
    """
    if username is None:
        username = state.user.username
    permissions = manage.list_permission(username=username, provided_permissions=state.user.permissions)
    return [f'{u.scope}/{u.operation}' for u in permissions]
