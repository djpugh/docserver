from functools import wraps
import logging
import typing

from starlette.requests import Request
from starlette.types import Scope

from docserver.permissions import OPERATIONS
from docserver.config import config


logger = logging.getLogger(__name__)


def get_permissions_from_request(request: typing.Union[Request, Scope]):
    mapped_permissions = {op: [] for op in OPERATIONS}
    if config.auth.enabled:
        try:
            if isinstance(request, Request):
                permissions = request.auth.scopes
            else:
                permissions = request['auth'].scopes
            for permission in permissions:
                if permission == 'authenticated':
                    continue
                scope, operation = permission.split('/')
                mapped_permissions[operation].append(scope)
        except AttributeError:
            logger.exception(f'Error extracting permissions from request {request}')
        logger.debug(f'Identified permissions {permissions}')    
    return mapped_permissions
