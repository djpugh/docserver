from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route

from docserver.config import config


async def logout(request:Request, *args):
    if config.auth.enabled and config.auth.provider.logout_url:
        return RedirectResponse(config.logout_url)
    else:
        return RedirectResponse('/login')


async def login(request:Request, *args):
    if config.auth.enabled:
        return config.auth.provider.login(request)
    else:
        return RedirectResponse('/')


async def login_callback(request: Request, *args):
    if config.auth.enabled:
        return config.auth.provider.login_callback(request)
    else:
        return RedirectResponse('/')


routes = [Route('/logout', endpoint=logout, methods=['GET']),
          Route('/login', endpoint=login, methods=['GET']),
          Route('/login/callback', endpoint=login_callback)]
