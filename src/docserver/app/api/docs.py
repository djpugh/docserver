import os
import shutil
from tempfile import TemporaryDirectory
from typing import List
import uuid

from itsdangerous import URLSafeSerializer
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import ValidationError
from starlette.requests import Request

from docserver.app.methods import ApplicationMethods
from docserver.app import schemas
from docserver.app.config import app_config

s = URLSafeSerializer(app_config.key, salt=app_config.salt)


router = APIRouter()
application_methods = ApplicationMethods()


@router.get('/list', response_model=List[schemas.ResponsePackage])
async def available_documentation():
    """
    List available packages
    """
    return application_methods.available_docs


@router.get('/{package}/versions', response_model=List[schemas.Version])
async def available_versions(package: str):
    """
    List available versions of a package
    """
    package = schemas.Package(name=package)
    return application_methods.get_versions(package)


# Lets add the ability to upload a package


@router.post('/upload', response_model=str, status_code=200)
async def register_package_upload(package: schemas.CreatePackage, request: Request):
    """
    Register a package upload
    """
    # We are going to return a redirect with an id that is encrypted based on a server secret key
    return f"Location: {request.url}/{s.dumps(package.dict())}"


@router.put('/upload/{upload_id}', response_model=str, status_code=201)
def upload_package(upload_id: str, request: Request, documentation: UploadFile = File(...)):
    result = None
    try:
        package_metadata = schemas.CreatePackage(**s.loads(upload_id))
        if os.path.splitext(documentation.filename)[-1] == '.zip':
            with TemporaryDirectory() as td:
                filename = os.path.join(td, f'{uuid.uuid4()}.zip')
                with open(filename, 'wb') as dest:
                    shutil.copyfileobj(documentation.file, dest)
                    dest.close()
                print(filename)
                slug = application_methods.save_documentation(filename, package_metadata)
                result = f"Location {request.url.scheme}://{request.url.hostname}/{slug}"
        else:
            raise HTTPException(status_code=401, detail=f'Incorrect filetype (must be zip archive) {documentation.filename}')
    except ValidationError:
        raise HTTPException(status_code=401, detail=f'Incorrect request for upload_id {package_metadata}')
    except PermissionError:
        if result:
            return result
        else:
            raise HTTPException(status_code=405, detail=f'Error parsing request')
