import logging
import os
import uuid


from docserver.auth.permissions import DEFAULTS


logger = logging.getLogger(__name__)


class AppConfigClass:

    docs_dir = os.getenv('DOCS_DIR', '/data/www/docs')
    search_index_dir = os.getenv('SEARCH_INDEX_DIR', '/data/www/search_indices')
    releases_only = os.getenv('DOCSERVER_ACCEPT_ALL', '0').lower() not in ['1', 'true']
    # How to make work in multi-threaded
    key = os.getenv('DOCSERVER_SAFE_KEY', str(uuid.uuid4()))
    salt = os.getenv('DOCSERVER_SALT', str(uuid.uuid4()))
    logout_url = os.getenv('WEBSITE_AUTH_LOGOUT_PATH', None)
    package_url_slug = '/packages'
    auth_enabled = os.getenv('DOCSERVER_AUTH_ENABLED', '1').lower() in ['1', 'true']
    default_write_permission = os.getenv('DOCSERVER_DEFAULT_WRITE_SCOPE', DEFAULTS['write'])
    default_read_permission = os.getenv('DOCSERVER_DEFAULT_READ_SCOPE', DEFAULTS['read'])
    default_delete_permission = os.getenv('DOCSERVER_DEFAULT_DELETE_SCOPE', DEFAULTS['delete'])
    auth_backend = os.getenv('DOCSERVER_AUTH_BACKEND', None)

app_config = AppConfigClass()
logger.debug(f'Authentication status: {app_config.auth_enabled}')
