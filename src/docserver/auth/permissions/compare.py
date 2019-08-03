from functools import wraps
import logging
import typing

from starlette.requests import Request
from starlette.types import Scope

from docserver.auth.permissions import OPERATIONS


logger = logging.getLogger(__name__)


def get_permissions_from_request(request: typing.Union[Request, Scope]):
    mapped_permissions = {op: [] for op in OPERATIONS}
    try:
        if isinstance(request, Request):
            permissions = request.auth.scopes
        else:
            permissions = request['auth'].scopes
        for permission in permissions:
            scope, operation = permission.split('/')
            mapped_permissions[operation].append(scope)
    except AttributeError:
        logger.exception(f'Error extracting permissions from request {request}')
    logger.debug(f'Identified permissions {permissions}')
    return mapped_permissions


def get_permissions(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        kwargs['provided_permissions'] = get_permissions_from_request(kwargs.pop('request'))
        return fn(*args, **kwargs)

    return wrapper
