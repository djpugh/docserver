import logging

from fastapi import APIRouter, Depends
from starlette.requests import Request

from docserver.api import schemas
from docserver.api.auth import auth_scheme
from docserver.auth.providers.base import APIAuthenticationCredentials
from docserver.permissions import manage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/add')
async def add_permission(body: schemas.PermissionManagement, credentials: APIAuthenticationCredentials = Depends(auth_scheme)):
    """
    Get an auth token
    """
    return manage.add_permission(username=body.username, permission=body.permission,
                                 provided_permissions=credentials.permissions)


@router.post('/remove')
async def remove_permission(body: schemas.PermissionManagement, credentials: APIAuthenticationCredentials = Depends(auth_scheme)):
    """
    Get an auth token
    """
    return manage.remove_permission(username=body.username, permission=body.permission,
                                    provided_permissions=credentials.permissions)

