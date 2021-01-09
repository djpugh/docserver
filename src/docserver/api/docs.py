import logging
import os
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import ValidationError
from starlette.requests import Request

from docserver import application_methods as methods
from docserver.api import schemas
from docserver.auth.authenticator import AuthenticationState, authenticator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/list', response_model=List[schemas.ResponsePackage])
async def available_documentation(request: Request, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """
    List available packages
    """
    results = methods.get_available_docs(provided_permissions=state.user.permissions)
    logger.debug(schemas.ResponsePackage.fields)
    return results


@router.get('/{package}/versions', response_model=List[schemas.Version])
async def available_versions(package_name: str, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """
    List available versions of a package
    """
    package = schemas.Package(name=package_name)
    return methods.get_versions(package, provided_permissions=state.user.permissions)


# Lets add the ability to upload a package


@router.post('/upload', response_model=str, status_code=200)
async def register_package_upload(package: schemas.PackageDocumentationVersion, request: Request, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    """
    Register a package upload
    """
    # We are going to return a redirect with an id that is encrypted based on a server secret key
    methods.register_package(package, provided_permissions=state.user.permissions)
    return f"Location: {request.url}/{package.serialize()}"


@router.put('/upload/{upload_id}', response_model=str, status_code=201)
def upload_package(upload_id: str, request: Request, documentation: UploadFile = File(...), state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    result = None
    try:
        package_metadata = schemas.PackageDocumentationVersion.from_serialized(upload_id)
        if os.path.splitext(documentation.filename)[-1] == '.zip':
            slug = methods.save_documentation(documentation, package_metadata, provided_permissions=state.user.permissions)
            result = f"Location {request.url.scheme}://{request.url.hostname}/{slug}"
        else:
            raise HTTPException(status_code=401, detail=f'Incorrect filetype (must be zip archive) {documentation.filename}')
    except ValidationError:
        raise HTTPException(status_code=401, detail=f'Incorrect request for upload_id {upload_id}')
    except PermissionError:
        if result:
            return result
        else:
            raise HTTPException(status_code=405, detail='Write Permission not available')


# Let's add deletion


@router.delete('{package_name}/{version}', status_code=200)
def delete_documentation_version(package_name: str, version: str, request: Request, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    documentation_version = schemas.BasePackageVersion(name=package_name, version=version)
    deleted = None
    try:
        deleted = methods.delete_version(documentation_version, provided_permissions=state.user.permissions)
    except PermissionError:
        raise HTTPException(status_code=405, detail='Delete Permission not available')
    if deleted:
        return {'Deleted': deleted}


@router.delete('{package_name}', status_code=200)
def delete_package(package_name: str, request: Request, state: AuthenticationState = Depends(authenticator.auth_backend.requires_auth())):
    package = schemas.BasePackage(name=package_name)
    deleted = None
    try:
        deleted = methods.delete_package(package, provided_permissions=state.user.permissions)
    except PermissionError:
        raise HTTPException(status_code=405, detail='Delete Permission not available')
    if deleted:
        return {'Deleted': deleted}
