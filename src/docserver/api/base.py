import os


from flask import Blueprint, url_for
from flask_restplus import Api as _Rapi
from flask_restplus import Resource
import pkg_resources

from docserver import __version__
API_VERSION = pkg_resources.parse_version(__version__).base_version.split('.')[0]


class Rapi(_Rapi):
    @property
    def specs_url(self):
        """
        Https hack
        Fixes issue where swagger-ui makes a call to swagger.json over HTTP.
        This can ONLY be used on servers that actually use HTTPS.
        On servers that use HTTP, this code should not be used at all.
        """
        if int(os.getenv('HTTPS', 0)):
            print('Using HTTPS monkeypatch')
            return url_for(self.endpoint('specs'), _external=True, _scheme='https')
        else:
            return super(Rapi, self).specs_url


# Specify the api based on the major version
blueprint = Blueprint('api', 'docserver', url_prefix=f'/api/v{API_VERSION}')
api = Rapi(blueprint,
           title='docserver API',
           version=__version__,
           description=f'Static documentation server ({__version__})',
           doc='/',
           contact=os.getenv('Owner', 'n/a'))


@api.route('/health')
class HealthCheck(Resource):

    def get(self):
        """
        Check service health
        """
        return {'status': 'ok'}


@api.route('/version')
class VersionCheck(Resource):

    def get(self):
        """
        Get the docserver version
        """
        return __version__
