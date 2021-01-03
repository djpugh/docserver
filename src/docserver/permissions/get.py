import logging
import typing

from starlette.requests import Request
from starlette.types import Scope

from docserver.auth.authenticator import authenticator
from docserver.config import config


logger = logging.getLogger(__name__)


def get_permissions_from_request(request: typing.Union[Request, Scope]):
    permissions = []
    if config.auth.enabled:
        try:
            if isinstance(request, Request):
                auth_state = authenticator.auth_backend.check(request)
                permissions = auth_state.user.permissions
            else:
                permissions = request['auth'].scopes
        except AttributeError:
            logger.exception(f'Error extracting permissions from request {request}')
        logger.debug(f'Identified permissions {permissions}')
    return permissions


def is_admin(permissions):
    return any([u.split('/')[1] == 'admin' for u in permissions])
