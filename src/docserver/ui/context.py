from docserver._version import get_versions
from docserver import config

__version__ = get_versions()['version']


def get_base_context():
     return {'app_name': config.config.app_name,
             'appname': config.config.app_name,
             'project_logo': config.config.logo,
             'auth': config.config.auth.enabled,
             'version': __version__,
            }
