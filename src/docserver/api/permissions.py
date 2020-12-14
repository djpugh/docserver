import logging

from fastapi import APIRouter, Depends

from docserver.api import schemas
from docserver.auth import authenticator, AuthenticationState
from docserver.permissions import manage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/add')
async def add_permission(body: schemas.PermissionManagement, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """
    Get an auth token
    """
    return manage.add_permission(username=body.username, permission=body.permission,
                                 provided_permissions=state.permissions)


@router.post('/remove')
async def remove_permission(body: schemas.PermissionManagement, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """
    Get an auth token
    """
    return manage.remove_permission(username=body.username, permission=body.permission,
                                    provided_permissions=state.permissions)
