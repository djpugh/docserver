import logging
import os
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import ValidationError
from starlette.requests import Request

from docserver import application_methods as methods
from docserver.api import schemas
from docserver.api.auth import auth_scheme
from docserver.auth.providers.base import APIAuthenticationCredentials

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/list', response_model=List[schemas.ResponsePackage])
async def available_documentation(request: Request, credentials: APIAuthenticationCredentials = Depends(auth_scheme)):
    """
    List available packages
    """
    results = methods.get_available_docs(provided_permissions=credentials.permissions)
    logger.debug(schemas.ResponsePackage.fields)
    return results


@router.get('/{package}/versions', response_model=List[schemas.Version])
async def available_versions(package_name: str, credentials: APIAuthenticationCredentials = Depends(auth_scheme)):
    """
    List available versions of a package
    """
    package = schemas.Package(name=package_name)
    return methods.get_versions(package, provided_permissions=credentials.permissions)


# Lets add the ability to upload a package


@router.post('/upload', response_model=str, status_code=200)
async def register_package_upload(package: schemas.CreatePackage, request: Request, credentials: APIAuthenticationCredentials = Depends(auth_scheme)):
    """
    Register a package upload
    """
    # We are going to return a redirect with an id that is encrypted based on a server secret key
    methods.register_package(package, provided_permissions=credentials.permissions)
    return f"Location: {request.url}/{package.serialize()}"


@router.put('/upload/{upload_id}', response_model=str, status_code=201)
def upload_package(upload_id: str, request: Request, documentation: UploadFile = File(...), credentials: APIAuthenticationCredentials = Depends(auth_scheme)):
    result = None
    try:
        package_metadata = schemas.CreatePackage.from_serialized(upload_id)
        if os.path.splitext(documentation.filename)[-1] == '.zip':
            slug = methods.save_documentation(documentation, package_metadata, provided_permissions=credentials.permissions)
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
