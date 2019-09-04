import logging

from fastapi import APIRouter
from starlette.requests import Request

from docserver.api import schemas
from docserver.config import config

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/token', response_model=schemas.TokenResponse)
async def token(request: Request):
    """
    Get an auth token
    """
    return config.auth.provider_object.get_token(request)

