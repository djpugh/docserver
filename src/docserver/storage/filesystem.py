import os
import shutil
from zipfile import ZipFile

from docserver.api import schemas


def save_docs(package: schemas.PackageDocumentationVersion, zipfile: str, ):
    # Need to have write permissions for the package
    path = make_path(package.get_path())
    zf = ZipFile(zipfile)
    for subfile in zf.namelist():
        zf.extract(subfile, path)
    zf.close()


def make_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def delete_docs(path):
    if os.path.exists(path):
        # Delete everything underneath that dir
        shutil.rmtree(path)
