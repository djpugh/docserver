import logging

from fastapi import APIRouter, Depends, HTTPException

from docserver.api import schemas
from docserver.auth.authenticator import AuthenticationState, authenticator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/token/upload', response_model=schemas.TokenResponse)
async def get_upload_token(state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth(allow_session=True))):
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
    result = authenticator.get_api_token(scopes=permissions)
    result['token_type'] = 'Bearer'
    logger.info(result)
    return result


@router.get('/token/validate')
async def validate_token(state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth(allow_session=False))):
    """Validate an auth token"""
    if state.is_authenticated():
        return {'detail': 'valid token'}
    raise HTTPException(status_code=403, detail='Invalid token')


@router.get('/me', response_model=schemas.UserResponse)
async def get_me(state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth(allow_session=True))):
    logger.info(state)
    return schemas.UserResponse.from_orm(state.user)
