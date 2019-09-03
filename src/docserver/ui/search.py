import os

from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.templating import Jinja2Templates

import docserver.application_methods as methods
from docserver.auth.decorators import requires
from docserver.permissions.get import get_permissions_from_request
from docserver.search.index import get_search_index_js
from docserver.ui.templates.nav import nav


templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


@requires('authenticated', redirect='login')
async def search_index(request: Request, *args, **kwargs):
    packages = methods.get_available_docs(provided_permissions=get_permissions_from_request(request))
    search_index_js = get_search_index_js(packages)
    return Response(search_index_js, media_type='text/javascript')


@requires('authenticated', redirect='login')
async def search(request: Request, *args, **kwargs):
    packages = methods.get_available_docs(provided_permissions=get_permissions_from_request(request))
    return templates.TemplateResponse('search.html', {'request': request, 'packages': packages,
                                                      'server_title': 'Docserver', 'nav': nav()})


routes = [Route("/searchindex.js", endpoint=search_index, methods=['GET']),
          Route("/search/", endpoint=search, methods=['GET'])]
