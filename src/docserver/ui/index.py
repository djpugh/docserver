import logging
import os
from pathlib import Path

from fastapi import HTTPException
from fastapi_aad_auth.ui.jinja import Jinja2Templates
from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route

from docserver.api import schemas
import docserver.application_methods as methods
from docserver.auth.authenticator import authenticator
from docserver.permissions.get import get_permissions_from_request
from docserver.ui.context import get_base_context


logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


@authenticator.auth_required()
async def index(request: Request, *args, **kwargs):
    permissions = get_permissions_from_request(request)
    packages = methods.get_available_docs(provided_permissions=permissions)
    context = get_base_context()
    context.update({'request': request, 'packages': packages})
    return templates.TemplateResponse('index.html', context)


@authenticator.auth_required()
async def upload(request: Request, *args, **kwargs):
    form_data = await request.form()
    logger.info(f'Processing form data {form_data}')
    if not form_data:
        return RedirectResponse('/')
    documentation = form_data['zipfile']
    if Path(documentation.filename).suffix.lower() != '.zip':
        raise HTTPException(status_code=401, detail=f'Incorrect filetype (must be zip archive) {documentation.filename}')
    create_package = schemas.PackageDocumentationVersion(name=form_data['packageName'],
                                                         repository=form_data['repositoryUrl'].replace(' ', '%20'),
                                                         tags=form_data['tags'].split(';'),
                                                         description=form_data['description'],
                                                         version=form_data['version'],
                                                         permissions=schemas.PermissionCollection(read_permission=form_data['permission'],
                                                                                                  write_permission=form_data['permission'],
                                                                                                  admin_permission=form_data['permission'])
                                                         )
    methods.register_package(create_package, provided_permissions=request.auth.scopes)
    slug = methods.save_documentation(documentation, create_package, provided_permissions=request.auth.scopes)
    logger.info(f'Slug: {slug}')
    return RedirectResponse(url=slug, status_code=303)


@authenticator.auth_required()
async def delete_version(request: Request, *args, **kwargs):
    form_data = await request.form()
    logger.info(f'Processing form data {form_data}')
    if not form_data:
        return RedirectResponse('/')
    documentation_version = schemas.BasePackageVersion(name=form_data['packageName'],
                                                       version=form_data['version'])
    methods.delete_version(documentation_version, provided_permissions=request.auth.scopes)
    return RedirectResponse(url='/', status_code=303)


@authenticator.auth_required()
async def delete_package(request: Request, *args, **kwargs):
    form_data = await request.form()
    logger.info(f'Processing form data {form_data}')
    if not form_data:
        return RedirectResponse('/')
    package = schemas.BasePackage(name=form_data['packageName'])
    methods.delete_package(package, provided_permissions=request.auth.scopes)
    return RedirectResponse(url='/', status_code=303)


routes = [Route("/", endpoint=index, methods=['GET', 'POST']),
          Route("/packages/", endpoint=index, methods=['GET']),
          Route("/_upload", endpoint=upload, methods=['POST']),
          Route("/_delete/package", endpoint=delete_package, methods=['POST']),
          Route("/_delete/version", endpoint=delete_version, methods=['POST'])]
