import os

from fastapi_aad_auth.ui.jinja import Jinja2Templates
from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.routing import Route

import docserver.application_methods as methods
from docserver.auth.authenticator import authenticator
from docserver.permissions.get import get_permissions_from_request
from docserver.ui.context import get_base_context


templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


@authenticator.auth_required()
async def index(request: Request, *args, **kwargs):
    packages = methods.get_available_docs(provided_permissions=get_permissions_from_request(request))
    context = get_base_context()
    context.update({'request': request, 'packages': packages})
    return templates.TemplateResponse('index.html', context)


routes = [Route("/", endpoint=index, methods=['GET']),
          Route("/packages/", endpoint=index, methods=['GET'])]
