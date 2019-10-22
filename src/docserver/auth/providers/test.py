import json
import logging


from starlette.authentication import AuthCredentials, SimpleUser

from docserver.auth.providers.base import BaseAuthenticationProvider
from docserver.auth.providers.config import ProviderConfig
from docserver.db.models import Permission


logger = logging.getLogger(__name__)


class TestConfig(ProviderConfig):
    pass


class TestProvider(BaseAuthenticationProvider):

    async def authenticate(self, request):
        logger.debug(request.headers)
        if "permissions" not in request.headers:
            auth = {'permissions': ['com/read']}
        else:
            auth = json.loads(request.headers["permissions"])
        permissions = []
        for permission in auth['permissions']:
            scope, operation = permission.split('/')
            permission = Permission.read_unique(dict(scope=scope, operation=operation))
            if permission:
                permissions.append(str(permission))
        logger.debug(f'Extracted permissions: {permissions}')
        return AuthCredentials(scopes=permissions), SimpleUser('auth')


entrypoint = (TestConfig, TestProvider)
