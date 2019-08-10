import json
import logging
import os

import msal
import requests
from starlette.authentication import (
    AuthenticationBackend, SimpleUser,
    AuthCredentials
)

from docserver.app.config import app_config
from docserver.db.models import Permission
from docserver.db.config import db_config


logger = logging.getLogger(__name__)


msal_application = msal.ConfidentialClientApplication(
    os.environ.get('DOCSERVER_AAD_CLIENT_ID'),
    authority=os.environ.get('DOCSERVER_AAD_AUTHORITY', 'https://login.microsoftonline.com/organizations'),
    client_credential=os.environ.get('DOCSERVER_AAD_CLIENT_SECRET'),
    # token_cache=...  # Default cache is in memory only.
    # You can learn how to use SerializableTokenCache from
    # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
    )


class AADAuthBackend(AuthenticationBackend):

    def __init__(self, config):
        self.config = config

    async def login(self, request):
        auth_state = str(uuid.uuid4())
        request.session['state'] = auth_state
        authorization_url = msal_application.get_authorization_request_url(self.config.scope, state=auth_state,
                                                                           redirect_uri=self.config.redirect_uri)
        return RedirectResponse(authorization_url)
    

    async def authenticate(self, request):
        # Get the user here
        # See if we are logged in:
        code = request.query_params.get('code', None)
        state = request.query_params.get('state', None)
        if state is None or code is None:
            return  # not authenticated
        if state != request.session['state']:
            raise ValueError("State does not match")
        # Get the user permissions here
        # TODO: simple implementation for AAD enabled app here 
        result = application.acquire_token_by_authorization_code(code, scopes=self.config.scope,redirect_uri=self.config.redirect_uri)
        # Role mapping
        
        # permission = Permission.read_unique(db_config.local_session(), dict(scope=scope, operation=operation))
        # if permission:
        #     permissions.append(str(permission))
        # logger.debug(f'Extracted permissions: {permissions}')
        # return AuthCredentials(scopes=permissions), SimpleUser('auth')


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
