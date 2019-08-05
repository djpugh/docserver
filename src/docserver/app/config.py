import os
import uuid


class AppConfigClass:

    docs_dir = os.getenv('DOCS_DIR', '/data/www/docs')
    releases_only = os.getenv('DOCSERVER_ACCEPT_ALL', '0').lower() not in ['1', 'true']
    key = os.getenv('DOCSERVER_KEY', str(uuid.uuid4()))
    salt = os.getenv('DOCSERVER_SALT', str(uuid.uuid4()))
    package_url_slug = '/packages'


app_config = AppConfigClass()
