import json
import logging


from starlette.authentication import (
    AuthenticationBackend, SimpleUser,
    AuthCredentials
)

from docserver.db.models import Permission
from docserver.db.config import db_config


logger = logging.getLogger(__name__)


class TestAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        logger.debug(request.headers)
        if "permissions" not in request.headers:
            auth = {'permissions': ['com/read']}
        else:
            auth = json.loads(request.headers["permissions"])
        permissions = []
        for permission in auth['permissions']:
            scope, operation = permission.split('/')
            permission = Permission.read_unique(db_config.local_session(), dict(scope=scope, operation=operation))
            if permission:
                permissions.append(str(permission))
        logger.debug(f'Extracted permissions: {permissions}')
        return AuthCredentials(scopes=permissions), SimpleUser('auth')


# class BasicAuthBackend(AuthenticationBackend):
#     async def authenticate(self, request):
#         if "Authorization" not in request.headers:
#             return
#
#         auth = request.headers["Authorization"]
#         try:
#             scheme, credentials = auth.split()
#             if scheme.lower() != 'basic':
#                 return
#             decoded = base64.b64decode(credentials).decode("ascii")
#         except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
#             raise AuthenticationError('Invalid basic auth credentials')
#
#         username, _, password = decoded.partition(":")
#         # TODO: You'd want to verify the username and password here,
#         #       possibly by installing `DatabaseMiddleware`
#         #       and retrieving user information from `request.database`.
#         return AuthCredentials(["authenticated"]), SimpleUser(username)
