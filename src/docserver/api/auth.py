import logging
from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from docserver.api import schemas
from docserver.auth.authenticator import AuthenticationState, authenticator
from docserver.auth.user import APIUser
from docserver.config import config

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/token', response_model=schemas.TokenResponse)
async def get_token(request: Request):
    """Get an auth token"""
    return config.auth.provider_object.get_token(request)


@router.get('/token/upload', response_model=schemas.TokenResponse)
async def get_upload_token(state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """Get an application level token for the API"""
    creds = state.user.permissions
    permissions = [u for u in creds if u.endswith('/write')]
    # Add any write credentials for any admin credentials
    permissions += [u.replace('/admin', '/write') for u in creds if u.endswith('/admin')]
    if not permissions:
        permissions = None
    logger.info(f'Credentials {creds}')
    logger.info(f'API Permissions {permissions}')
    if permissions is None:
        raise PermissionError('Not authorised to create an API token')
    token = config.auth.provider_object.get_api_token(scopes=permissions)
    return {'access_token': token, 'token_type': 'Bearer', 'expires_in': config.auth.token_lifetime}


@router.get('/token/validate')
async def validate_token(state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """Validate an auth token"""
    if config.auth.provider_object.validate_token(state.credentials):
        return {'detail': 'valid token'}
    raise HTTPException(status_code=403, detail='Invalid token')


@router.get('/me', response_model=Union[schemas.UserResponse, APIUser])
async def get_me(state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    return config.auth.provider_object.authenticate_token(state.credentials).user
