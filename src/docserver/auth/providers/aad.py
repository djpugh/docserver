import json
import logging
import os
from typing import List
import uuid

from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.models import OAuthFlowAuthorizationCode as OAuthFlowAuthorizationCodeModel
import msal
from pydantic import UrlStr
from starlette.responses import RedirectResponse

from docserver.auth.providers.base import AuthState, BaseAuthenticationProvider
from docserver.auth.providers.config import ProviderConfig


logger = logging.getLogger(__name__)


# class AADAuthorizationCodeModel(OAuthFlowAuthorizationCodeModel):
#
#     client_id: str = os.environ.get('DOCSERVER_AAD_CLIENT_ID', ***REMOVED***)
#     authority: UrlStr = os.environ.get('DOCSERVER_AAD_AUTHORITY', 'https://login.microsoftonline.com/organizations')
#     client_secret: str = os.environ.get('DOCSERVER_AAD_CLIENT_SECRET', ***REMOVED***)
#     redirect_url: UrlStr = ''
#     tokenUrl = None


# class AADAuthConfig(OAuthConfig):
#     flow: OAuthFlowsModel = OAuthFlowsModel(authorizationCode=AADAuthorizationCodeModel())
#     login_url: UrlStr
#     logout_url: UrlStr
#     scope: List[str]


class AADAuth(AuthState):
    pass


class AADConfig(ProviderConfig):
    pass


class AADAuthProvider(BaseAuthenticationProvider):

    def __init__(self, config, *args, **kwargs):
        self.config = config
        self.msal_application = msal.ConfidentialClientApplication(
            self.config.client_id,
            authority=self.config.authority,
            client_credential=self.config.client_secret)

    def login(self, request):
        auth_state = self.pro
        auth_state = AADAuth(login_redirect=redirect)
        request.session['auth'] = auth_state.store()
        authorization_url = self.msal_application.get_authorization_request_url(self.config.scope, state=auth_state.session_state,
                                                                                redirect_uri=self.config.redirect_uri)
        return RedirectResponse(authorization_url, )

    async def authenticate(self, *args, **kwargs):
        print(self, args, kwargs)
        # Get the user here
        # See if we are logged in:

    def login_callback(self, request):
        code = request.query_params.get('code', None)
        state = request.query_params.get('state', None)
        if state is None or code is None:
            return  # not authenticated
        auth_state = AADAuth.load(request.session.get('auth', AADAuth().store))
        auth_state.check_session_state(state)
        # Get the user permissions here
        # TODO: simple implementation for AAD enabled app here 
        result = self.msal_application.acquire_token_by_authorization_code(code, scopes=self.config.scope,
                                                                           redirect_uri=self.config.redirect_uri)
        return result


entrypoint = (AADConfig, AADAuthProvider)