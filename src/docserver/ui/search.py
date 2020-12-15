import os

from fastapi_aad_auth.ui.jinja import Jinja2Templates
from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

import docserver.application_methods as methods
from docserver.auth.authenticator import authenticator
from docserver.config import config
from docserver.permissions.get import get_permissions_from_request
from docserver.search.index import get_search_index_js
from docserver.ui.templates.nav import nav


templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


@authenticator.auth_required()
async def search_index(request: Request, *args, **kwargs):
    packages = methods.get_available_docs(provided_permissions=get_permissions_from_request(request))
    search_index_js = get_search_index_js(packages)
    return Response(search_index_js, media_type='text/javascript')


@authenticator.auth_required()
async def search(request: Request, *args, **kwargs):
    packages = methods.get_available_docs(provided_permissions=get_permissions_from_request(request))
    return templates.TemplateResponse('search.html', {'request': request, 'packages': packages,
                                                      'app_name': config.app_name, 'nav': nav(config.logo)})


routes = [Route("/searchindex.js", endpoint=search_index, methods=['GET']),
          Route("/search/", endpoint=search, methods=['GET'])]
