import os

from fastapi import FastAPI
from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from docserver import DOCS_DIR, db, __version__
from docserver.api import base_api, docs_api

if 'untagged' in __version__:
    major_version = 0
else:
    major_version = __version__.split('.')[0]

app = FastAPI(title='Documentation Server',
              description='Documentation Server allowing upload of static html documentation',
              version=__version__,
              openapi_url=f"/api/v{major_version}/openapi.json",
              docs_url='/api/docs',
              redoc_url='/api/redoc')

templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.templates', 'index.html')))


@app.route("/")
@app.route("/packages/")
async def list_docs(request: Request, *args, **kwargs):
    print(args, kwargs)
    session = db.SessionLocal()
    packages = session.query(db.models.Package).order_by(db.models.Package.name).all()
    print(packages)
    return templates.TemplateResponse('index.html', {'request': request, 'packages': packages})


app.include_router(base_api)
app.include_router(docs_api, prefix='/api', tags=['api'])
if not os.path.exists(DOCS_DIR):
    os.mkdir(DOCS_DIR)
app.mount('/packages', StaticFiles(directory=DOCS_DIR, html=True))
