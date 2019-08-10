import logging
import os
from warnings import warn

from fastapi import FastAPI
from pkg_resources import resource_filename, iter_entry_points
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware.authentication import AuthenticationMiddleware

from docserver import __version__
from docserver.app.api import base_api, docs_api
from docserver.app.config import app_config
from docserver.app.methods import ApplicationMethods
from docserver.auth.backends.basic import TestAuthBackend
from docserver.auth.staticfiles import PermissionedStaticFiles, DBPermissionsCheck
from docserver.db.config import db_config
from docserver.ui.help import build_help
from docserver.ui.templates.nav import nav


AUTH_ENTRYPOINT = 'docserver.auth.backends'


logging.basicConfig(level='DEBUG')

application_methods = ApplicationMethods()

if 'untagged' in __version__ or 'unknown':
    major_version = 0
else:
    major_version = __version__.split('.')[0]

app = FastAPI(title='Documentation Server',
              description='Documentation Server allowing upload of static html documentation',
              version=__version__,
              openapi_url=f"/api/v{major_version}/openapi.json",
              docs_url='/api/docs',
              redoc_url='/api/redoc')

templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


@app.route("/")
@app.route("/packages/")
async def list_docs(request: Request, *args, **kwargs):
    packages = application_methods.get_available_docs(request=request)
    return templates.TemplateResponse('index.html', {'request': request, 'packages': packages,
                                                     'server_title': 'Docserver', 'nav': nav()})

# TODO we need to set these programatically and warn when using TestAuthBackend


@app.route("/searchindex.js")
async def search_index(request: Request, *args, **kwargs):
    packages = application_methods.get_available_docs(request=request)
    search_index_js = application_methods.get_search_index_js(packages)
    return Response(search_index_js, media_type='text/javascript')


@app.route("/search/")
async def search(request: Request, *args, **kwargs):
    packages = application_methods.get_available_docs(request=request)
    return templates.TemplateResponse('search.html', {'request': request, 'packages': packages,
                                                      'server_title': 'Docserver', 'nav': nav()})


@app.route('/logout')
async def logout(*args):
    if app_config.auth_enabled and app_config.logout_url:
        return RedirectResponse(app_config.logout_url)
    else:
        return RedirectResponse('/')

if app_config.auth_enabled:
    # Lets load in the backend
    backend = None
    for ep in iter_entry_points(AUTH_ENTRYPOINT):
        if ep.name.lower() == app_config.auth_backend.lower():
            backend = ep.load()
            break
    if not backend:
        raise ValueError('No authentication backend selected, this is required for the authentication middleware and will process the request and authenticate it')
    if TestAuthBackend in backend.__mro__:
        warn('TestAuthBackend is not suitable for production environments')
    app.add_middleware(AuthenticationMiddleware, backend=TestAuthBackend())

app.include_router(base_api)
app.include_router(docs_api, prefix='/api', tags=['api'])
if not os.path.exists(app_config.docs_dir):
    os.mkdir(app_config.docs_dir)
# We need to add some role based access heres
app.mount(app_config.package_url_slug, PermissionedStaticFiles(permissions_check=DBPermissionsCheck(db_config.local_session), directory=app_config.docs_dir, html=True))
app.mount('/static', StaticFiles(directory=os.path.dirname(resource_filename('docserver.ui.static', 'index.html'))))
build_help()
app.mount('/help', StaticFiles(directory=os.path.join(os.path.dirname(resource_filename('docserver.ui.help',
                                                                                        'index.html')), 'html'),
                               html=True))
