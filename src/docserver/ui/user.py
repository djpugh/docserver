import os

from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.routing import Route
from starlette.templating import Jinja2Templates

from docserver.auth.decorators import auth_required
from docserver.config import config
from docserver.ui.templates.nav import nav


templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


@auth_required
async def user(request: Request, *args, **kwargs):
    user = config.auth.provider_object.auth_state_klass.load_from_session(config.auth.serializer, request.session).user
    return templates.TemplateResponse('user.html', {'request': request, 'app_name': config.app_name,
                                                    'user': user,
                                                    'nav': nav()})


routes = [Route("/me/", endpoint=user, methods=['GET'])]
