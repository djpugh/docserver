from docserver import _patch
from docserver import db  # noqa F401
from docserver._copyright import get_copyright
from docserver._version import get_versions

__copyright__ = get_copyright()
__version__ = get_versions()['version']
del get_versions
del get_copyright
del _patch
