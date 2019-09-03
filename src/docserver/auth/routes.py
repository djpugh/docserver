from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route

from docserver.config import config


async def logout(request:Request, *args):
    if config.auth.enabled and config.auth.provider.logout_url:
        return RedirectResponse(config.auth.provider.logout_url)
    else:
        return RedirectResponse('/login')


async def login(request: Request, *args):
    print('Logging in')
    if config.auth.enabled and not config.auth.provider_object.is_authenticated(request):
        return config.auth.provider_object.login(request)
    else:
        return RedirectResponse('/')


async def login_callback(request: Request, *args):
    if config.auth.enabled:
        return config.auth.provider_object.process_login_callback(request)
    else:
        return RedirectResponse('/')


routes = [Route('/logout', endpoint=logout, methods=['GET']),
          Route('/login', endpoint=login, methods=['GET']),
          Route('/login/redirect', endpoint=login_callback)]
