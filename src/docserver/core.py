import json
import logging
import os
import subprocess  # nosec subprocess used for fixed initialisation command
import sys

from fastapi import FastAPI
from pkg_resources import resource_filename
from ruamel import yaml
from starlette.staticfiles import StaticFiles

from docserver._version import get_versions
from docserver.api import api_version
from docserver.api.auth import router as auth_api
from docserver.api.base import router as base_api
from docserver.api.docs import router as docs_api
from docserver.api.permissions import router as permissions_api
from docserver.auth.authenticator import authenticator
from docserver.config import config
from docserver.errors.handlers import register as register_error_handlers
from docserver.permissions.staticfiles import DBPermissionsCheck, LoggedInPermissionsCheck, PermissionedStaticFiles
from docserver.ui.index import routes as index_routes
from docserver.ui.search import routes as search_routes

AUTH_ENTRYPOINT = 'docserver.auth.backends'

__version__ = get_versions()['version']

logging.basicConfig(level='DEBUG')
logging.info(f'Running docserver version {__version__}')
logging.info(f'Config:\n{yaml.round_trip_dump(json.loads(config.json()))}')

app = FastAPI(title='Documentation Server',
              description='Documentation Server allowing upload of static html documentation',
              version=__version__,
              openapi_url=f"/api/v{api_version}/openapi.json",
              docs_url='/api/docs',
              redoc_url='/api/redoc',
              routes=index_routes+search_routes)

register_error_handlers(app)
app.include_router(base_api, prefix='/api')
app.include_router(docs_api, prefix='/api/docs', tags=['docs'])
app.include_router(permissions_api, prefix='/api/permissions', tags=['permissions'])

if config.auth.enabled:
    authenticator.configure_app(app)
    app.include_router(auth_api, prefix='/api/auth', tags=['auth'])
if not os.path.exists(config.upload.docs_dir):
    os.mkdir(config.upload.docs_dir)
# We need to add some role based access heres
app.mount(config.upload.package_url_slug,
          PermissionedStaticFiles(permissions_check=DBPermissionsCheck(config.db.local_session),
                                  directory=config.upload.docs_dir, html=True))
app.mount('/static', StaticFiles(directory=os.path.dirname(resource_filename('docserver.ui.static', 'index.html'))))
if config.help_dir is None:
    logging.info('Building Docs')
    subprocess.check_call([sys.executable, '-m', 'docserver.ui.help'])  # nosec
    logging.info('Docs built')
    app.mount('/help', PermissionedStaticFiles(permissions_check=LoggedInPermissionsCheck(),
                                               directory=os.path.join(os.path.dirname(resource_filename('docserver.ui.help',
                                                                                                        'index.html')), 'html'),
                                               html=True))
else:
    app.mount('/help', StaticFiles(directory=config.help_dir, html=True))
logging.info('Application ready')
