import logging

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route

from docserver.config import config


logger = logging.getLogger(__name__)


async def logout(request:Request, *args):
    if config.auth.enabled:
        config.auth.provider_object.logout(request)
    return RedirectResponse('/splash')


async def login(request: Request, *args):
    logger.debug(f'Logging in - request url {request.url}')
    if config.auth.enabled:
        logger.debug(f'Auth {request.auth}')
        return config.auth.provider_object.login(request)
    else:
        logger.debug('Auth not enabled')
        return RedirectResponse('/')


async def login_callback(request: Request, *args):
    logger.debug(f'Processing login callback - request url {request.url}')
    if config.auth.enabled:
        logger.debug(f'Auth {request.auth}')
        return config.auth.provider_object.process_login_callback(request)
    else:
        logger.debug('Auth not enabled')
        return RedirectResponse('/')


routes = [Route('/logout', endpoint=logout, methods=['GET']),
          Route('/login', endpoint=login, methods=['GET']),
          Route('/login/redirect', endpoint=login_callback)]
