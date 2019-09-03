import logging
import os

from fastapi import FastAPI
from pkg_resources import resource_filename
from starlette.staticfiles import StaticFiles

from docserver import __version__
from docserver.api import api_version
from docserver.api.base import router as base_api
from docserver.api.base import router as docs_api
from docserver.auth.routes import routes as auth_routes
from docserver.config import config
from docserver.permissions.staticfiles import PermissionedStaticFiles, DBPermissionsCheck
from docserver.ui.help import build_help
from docserver.ui.index import routes as index_routes
from docserver.ui.search import routes as search_routes

AUTH_ENTRYPOINT = 'docserver.auth.backends'


logging.basicConfig(level='DEBUG')


app = FastAPI(title='Documentation Server',
              description='Documentation Server allowing upload of static html documentation',
              version=__version__,
              openapi_url=f"/api/v{api_version}/openapi.json",
              docs_url='/api/docs',
              redoc_url='/api/redoc',
              routes=index_routes+search_routes+auth_routes)

config.auth.set_middleware(app)

app.include_router(base_api)
app.include_router(docs_api, prefix='/api', tags=['api'])
if not os.path.exists(config.upload.docs_dir):
    os.mkdir(config.upload.docs_dir)
# We need to add some role based access heres
app.mount(config.upload.package_url_slug,
          PermissionedStaticFiles(permissions_check=DBPermissionsCheck(config.db.local_session),
                                  directory=config.upload.docs_dir, html=True))
app.mount('/static', StaticFiles(directory=os.path.dirname(resource_filename('docserver.ui.static', 'index.html'))))
build_help()
app.mount('/help', StaticFiles(directory=os.path.join(os.path.dirname(resource_filename('docserver.ui.help',
                                                                                        'index.html')), 'html'),
                               html=True))
