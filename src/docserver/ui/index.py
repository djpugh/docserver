import os

from fastapi_aad_auth.ui.jinja import Jinja2Templates
from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.routing import Route

import docserver.application_methods as methods
from docserver.auth.authenticator import authenticator
from docserver.config import config
from docserver.permissions.get import get_permissions_from_request
from docserver.ui.templates.nav import nav


templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


@authenticator.auth_required()
async def index(request: Request, *args, **kwargs):
    packages = methods.get_available_docs(provided_permissions=get_permissions_from_request(request))
    return templates.TemplateResponse('index.html', {'request': request, 'packages': packages,
                                                     'app_name': config.app_name, 'nav': nav(config.logo)})


routes = [Route("/", endpoint=index, methods=['GET']),
          Route("/packages/", endpoint=index, methods=['GET'])]
