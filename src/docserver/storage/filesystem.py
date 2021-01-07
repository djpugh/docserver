import os
from zipfile import ZipFile

from docserver.api import schemas
from docserver.config import config


def save_docs(package: schemas.PackageDocumentationVersion, zipfile: str, ):
    # Need to have write permissions for the package
    path = make_path(package.get_path())
    zf = ZipFile(zipfile)
    for subfile in zf.namelist():
        zf.extract(subfile, path)
    zf.close()


def make_path(path):
    required_dir = os.path.join(config.upload.docs_dir, path)
    if not os.path.exists(required_dir):
        os.makedirs(required_dir)
    return required_dir
