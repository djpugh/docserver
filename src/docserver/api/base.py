from fastapi import APIRouter, Depends

from docserver._version import get_versions
from docserver.auth.authenticator import AuthenticationState, authenticator

__version__ = get_versions()['version']

router = APIRouter()


@router.get('/health')
async def health_check():
    """
    Check service health
    """
    return {'status': 'ok'}


@router.get('/version')
async def get_version(state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth(allow_session=True))):
    """
    Get the docserver version
    """
    return __version__
