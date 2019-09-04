import logging
import os
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import ValidationError
from starlette.requests import Request

from docserver.api import schemas
import docserver.application_methods as methods

logger = logging.getLogger(__name__)
router = APIRouter()

# TODO: update logging
# TODO: implement aad backend
# TODO: implement oauth backend (?) & github?


@router.get('/list', response_model=List[schemas.ResponsePackage])
async def available_documentation(request: Request):
    """
    List available packages
    """
    results = methods.get_available_docs()
    logger.debug(schemas.ResponsePackage.fields)
    return results


@router.get('/{package}/versions', response_model=List[schemas.Version])
async def available_versions(package_name: str, request: Request):
    """
    List available versions of a package
    """
    package = schemas.Package(name=package_name)
    return methods.get_versions(package)


# Lets add the ability to upload a package


@router.post('/upload', response_model=str, status_code=200)
async def register_package_upload(package: schemas.CreatePackage, request: Request):
    """
    Register a package upload
    """
    # We are going to return a redirect with an id that is encrypted based on a server secret key
    methods.register_package(package)
    return f"Location: {request.url}/{package.serialize()}"


@router.put('/upload/{upload_id}', response_model=str, status_code=201)
def upload_package(upload_id: str, request: Request, documentation: UploadFile = File(...)):
    result = None
    try:
        package_metadata = schemas.CreatePackage.from_serialized(upload_id)
        if os.path.splitext(documentation.filename)[-1] == '.zip':
            slug = methods.save_documentation(documentation, package_metadata)
            result = f"Location {request.url.scheme}://{request.url.hostname}/{slug}"
        else:
            raise HTTPException(status_code=401, detail=f'Incorrect filetype (must be zip archive) {documentation.filename}')
    except ValidationError:
        raise HTTPException(status_code=401, detail=f'Incorrect request for upload_id {upload_id}')
    except PermissionError:
        if result:
            return result
        else:
            raise HTTPException(status_code=405, detail=f'Write Permission not available')
