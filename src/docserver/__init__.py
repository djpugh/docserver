import os

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from docserver import db
DOCS_DIR = os.getenv('DOCS_DIR', '/data/www/docs')