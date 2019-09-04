import os

from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from docserver.config import config

templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


async def splash(request: Request, *args, **kwargs):
    if not config.auth.enabled or config.auth.provider_object.check_state(request):
        # This is authenticated so go straight to the homepage
        return RedirectResponse('/')
    return templates.TemplateResponse('splash.html', {'request': request, 'app_name': config.app_name,
                                                      'login': config.auth.provider_object.login_html})


routes = [Route("/splash", endpoint=splash, methods=['GET'])]