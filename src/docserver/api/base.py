from fastapi import APIRouter
import pkg_resources

from docserver import __version__
API_VERSION = pkg_resources.parse_version(__version__).base_version.split('.')[0]


router = APIRouter()


@router.get('/health')
async def health_check():
    """
    Check service health
    """
    return {'status': 'ok'}


@router.get('/version')
async def get_version():
    """
    Get the docserver version
    """
    return __version__
