from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
import pkg_resources

from docserver import __version__
from docserver.api.auth import auth_scheme
API_VERSION = pkg_resources.parse_version(__version__).base_version.split('.')[0]


router = APIRouter()


@router.get('/health')
async def health_check():
    """
    Check service health
    """
    return {'status': 'ok'}


@router.get('/version')
async def get_version(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """
    Get the docserver version
    """
    return __version__
