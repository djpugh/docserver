from functools import partial
import logging

from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import request_response, Route

from docserver.auth.decorators import auth_required
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


def wrapper_factory(endpoint):

    @auth_required
    async def req_wrapper(request: Request, *args, **kwargs):
        if not config.auth.enabled or config.auth.provider_object.check_state(request):
            print(endpoint)
            return await endpoint(request, *args, **kwargs)
        else:
            return RedirectResponse('/splash')

    return req_wrapper


def app_routes_add_auth(app, route_list, ignore=False):
    if config.auth.enabled:
        routes = app.router.routes
        for i, route in enumerate(routes):
            # Can use allow list or block list (i.e. ignore = True sets all except the route list to have auth
            if (route.name in route_list and not ignore) or (route.name not in route_list and ignore):
                route.endpoint = wrapper_factory(endpoint=route.endpoint)
                route.app = request_response(route.endpoint)
            app.router.routes[i] = route
