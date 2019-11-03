import logging
import typing

from starlette.requests import Request
from starlette.types import Scope

from docserver.config import config


logger = logging.getLogger(__name__)


def get_permissions_from_request(request: typing.Union[Request, Scope]):
    permissions = []
    if config.auth.enabled:
        try:
            if isinstance(request, Request):
                permissions = request.auth.scopes
            else:
                permissions = request['auth'].scopes
        except AttributeError:
            logger.exception(f'Error extracting permissions from request {request}')
        logger.debug(f'Identified permissions {permissions}')
    return permissions
