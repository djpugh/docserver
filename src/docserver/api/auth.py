import logging
from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from docserver.api import schemas
from docserver.auth.state import User, APIUser
from docserver.auth.providers.base import APIAuthenticator, APIAuthenticationCredentials
from docserver.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

auth_scheme = APIAuthenticator()


@router.get('/token', response_model=schemas.TokenResponse)
async def get_token(request: Request):
    """Get an auth token"""
    return config.auth.provider_object.get_token(request)


@router.get('/token/api', response_model=schemas.TokenResponse)
async def get_token(credentials: APIAuthenticationCredentials = Depends(auth_scheme)):
    """Get an application level token for the API"""
    permissions = [u for u in credentials.credentials if u.endswith('/write')]
    # Add any write credentials for any admin credentials
    permissions += [u.replace('/admin', '/write') for u in credentials.credentials if u.endswith('/admin')]
    if not permissions:
        permissions = None
    if permissions is None:
        raise PermissionError('Not authorised to create an API token')
    token = config.auth.provider_object.get_api_token(scopes=permissions)
    return {'access_token': token, 'token_type': 'Bearer', 'expires_in': config.auth.token_lifetime}


@router.get('/token/validate')
async def validate_token(credentials: APIAuthenticationCredentials = Depends(auth_scheme)):
    """Validate an auth token"""
    if config.auth.provider_object.validate_token(credentials.credentials):
        return {'detail': 'valid token'}
    raise HTTPException(status_code=403, detail=f'Invalid token')


@router.get('/me', response_model=Union[schemas.UserResponse, APIUser])
async def get_me(credentials: APIAuthenticationCredentials = Depends(auth_scheme)):
    return config.auth.provider_object.authenticate_token(credentials.credentials).user
