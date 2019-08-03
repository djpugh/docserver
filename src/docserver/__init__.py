from ._version import get_versions
from docserver import _patch
from docserver import db  # noqa F401
__version__ = get_versions()['version']
del get_versions
del _patch
