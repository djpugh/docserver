import os
from tempfile import TemporaryDirectory
import uuid
import shutil

from itsdangerous import URLSafeSerializer
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from starlette.requests import Request

from docserver.core import docs_information

s = URLSafeSerializer(os.getenv('DOCSERVER_KEY', 'random'), salt=os.getenv('DOCSERVER_SALT', 'salt'))


class PackageModel(BaseModel):
    package: str
    version: str
    repository: str
    language: str


router = APIRouter()


@router.get('/list')
async def available_documentation():
    """
    List available packages
    """
    return docs_information.available_docs


@router.route('/{package}/versions')
async def available_versions(package):
    """
    List available versions of a package
    """
    return docs_information.get_versions(package)


# Lets add the ability to upload a package


@router.post('/upload', status_code=200)
async def register_package_upload(metadata: PackageModel, request: Request):
    """
    Register a package upload
    """
    # We are going to return a redirect with an id that is encrypted based on a server secret key
    validated_metadata, path = docs_information.validate_metadata(metadata)
    return f"Location: {request.url}/{s.dumps(validated_metadata.dict())}"


@router.put('/upload/{upload_id}', status_code=201)
def upload_package(upload_id: str, request: Request, documentation: UploadFile = File(...)):
    package_metadata = s.loads(upload_id)
    if sorted(list(package_metadata.keys())) == ['language', 'package', 'repository', 'version']:
        if os.path.splitext(documentation.filename)[-1] == '.zip':
            with TemporaryDirectory() as td:
                filename = os.path.join(td, f'{uuid.uuid4()}.zip')
                with open(filename, 'wb') as dest:
                    shutil.copyfileobj(documentation.file, dest)
                    dest.close()
                print(filename)
                slug = docs_information.save_documentation(filename, PackageModel(**package_metadata))
            return f"Location {request.url.scheme}://{request.url.hostname}/{slug}"
        else:
            raise HTTPException(status_code=401, detail=f'Incorrect filetype (must be zip archive) {documentation.filename}')
    else:
        raise HTTPException(status_code=401, detail='Incorrect request for upload_id')
