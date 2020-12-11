import os

from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.routing import Route
from starlette.templating import Jinja2Templates

import docserver.application_methods as methods
from docserver.auth.decorators import auth_required
from docserver.config import config
from docserver.permissions.get import get_permissions_from_request
from docserver.ui.templates.nav import nav


templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


@auth_required
async def index(request: Request, *args, **kwargs):
    packages = methods.get_available_docs(provided_permissions=get_permissions_from_request(request))
    return templates.TemplateResponse('index.html', {'request': request, 'packages': packages,
                                                     'app_name': config.app_name, 'nav': nav()})


@auth_required
async def frame(request: Request, *args, **kwargs):
    packages = methods.get_available_docs(provided_permissions=get_permissions_from_request(request))
    return templates.TemplateResponse('frame.html', {'request': request, 'path': '/packages/test/0.1.0',
                                                     'app_name': config.app_name, 'nav': nav()})


routes = [Route("/", endpoint=index, methods=['GET']),
          Route("/view", endpoint=frame, methods=['GET']),
          Route("/packages/", endpoint=index, methods=['GET']),
          Route("/login/None", endpoint=index, methods=['GET'])]
