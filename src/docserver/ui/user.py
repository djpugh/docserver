import os

from fastapi.security import HTTPBearer
from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from docserver.auth.decorators import auth_required
from docserver.auth.providers.base import APIAuthenticator
from docserver.config import config
from docserver.permissions.get import get_permissions_from_request
from docserver.search.index import get_search_index_js
from docserver.ui.templates.nav import nav


templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


@auth_required
async def user(request: Request, *args, **kwargs):
    user = config.auth.provider_object.auth_state_klass.load_from_session(config.auth.serializer, request.session).user
    return templates.TemplateResponse('user.html', {'request': request, 'app_name': config.app_name,
                                                    'user': user,
                                                    'nav': nav()})


routes = [Route("/me/", endpoint=user, methods=['GET'])]
