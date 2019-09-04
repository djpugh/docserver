import logging
import os
from pathlib import Path
from typing import List

import msal
from pydantic import UrlStr, Schema, SecretStr, validator
from starlette.responses import RedirectResponse

from docserver.auth.providers.base import BaseAuthenticationProvider
from docserver.auth.providers.config import ProviderConfig
from docserver.auth.state import AuthenticationOptions, AuthState, User
from docserver.config import config

logger = logging.getLogger(__name__)


class AADAuth(AuthState):

    def set_user_from_response(self, jwt):
        name = jwt['id_token_claims']['name']
        email = jwt['id_token_claims']['preferred_username']
        roles = jwt['id_token_claims'].get('app_roles', [])
        user = User(name=name, email=email, roles=roles)
        self.user = user
        self.state = AuthenticationOptions.authenticated


class AADConfig(ProviderConfig):
    client_id: SecretStr = Schema(SecretStr(os.environ.get('DOCSERVER_AAD_CLIENT_ID')))
    authority: UrlStr = Schema(UrlStr(os.environ.get('DOCSERVER_AAD_AUTHORITY',
                                                     'https://login.microsoftonline.com/organizations')))
    scope: List[str] = ["https://graph.microsoft.com/.default"]
    client_secret: SecretStr = Schema(SecretStr(os.environ.get('DOCSERVER_AAD_CLIENT_SECRET')))
    redirect_url: UrlStr = Schema(UrlStr(f"{config.host_name}/login/redirect"))
    token_url: UrlStr = None
    cache_file: Path = Schema(os.environ.get('DOCSERVER_AAD_CACHE_PATH', None))
    # login_url: UrlStr
    # logout_url: UrlStr

    @validator('cache_file', pre=True, always=True)
    def validate_cache_file(cls, value):
        if value:
            return Path(value)
        else:
            return Path.cwd() / 'cache.bin'


class AADAuthProvider(BaseAuthenticationProvider):

    def __init__(self, *args, **kwargs):
        super().__init__(auth_state_klass=AADAuth)
        # cache = msal.SerializableTokenCache()
        # if os.path.exists(config.auth.provider.cache_file):
        #     cache.deserialize(open(config.auth.provider.cache_file, "r").read())
        # atexit.register(lambda:
        #                 open(config.auth.provider.cache_file, "w").write(cache.serialize())
        #                 # The following line persists only when state changed
        #                 if cache.has_state_changed else None)

        self.msal_application = msal.ConfidentialClientApplication(
            config.auth.provider.client_id.get_secret_value(),
            authority=config.auth.provider.authority,
            client_credential=config.auth.provider.client_secret.get_secret_value())
            # token_cache=cache)

    def login(self, request):
        logger.debug(f'Logging in - request url {request.url}')
        auth_state = self.auth_state_klass.load_from_session(config.auth.serializer, request.session)
        if not auth_state.redirect:
            auth_state.redirect = str('/')
        if auth_state.is_authenticated():
            redirect = str(auth_state.redirect)
            if redirect.endswith('/login'):
                redirect = '/'
            logger.info(f'Logged in, redirecting to {redirect}')
            return RedirectResponse(redirect)
        else:
            logger.debug(f'state {auth_state}')
            auth_state.save_to_session(config.auth.serializer, request.session)
            authorization_url = self.msal_application.get_authorization_request_url(config.auth.provider.scope,
                                                                                    state=auth_state.session_state,
                                                                                    redirect_uri=config.auth.provider.redirect_url)
            return RedirectResponse(authorization_url)

    def process_login_callback(self, request):
        logger.debug(f'Starting login callback - {request.url}')
        code = request.query_params.get('code', None)
        state = request.query_params.get('state', None)
        if state is None or code is None:
            return  # not authenticated
        auth_state = self.auth_state_klass.load_from_session(config.auth.serializer, request.session)
        auth_state.check_session_state(state)
        result = self.msal_application.acquire_token_by_authorization_code(code, scopes=config.auth.provider.scope,
                                                                           redirect_uri=config.auth.provider.redirect_url)
        # Get the user permissions here
        auth_state.set_user_from_response(result)
        auth_state.save_to_session(config.auth.serializer, request.session)
        logger.debug(f'State {auth_state} - Authenticated = {self.is_authenticated(request)}')
        redirect = str(auth_state.redirect)
        if not redirect:
            redirect = '/'
        logger.debug(f'Redirecting to {redirect}')
        return RedirectResponse(redirect)

    @property
    def login_html(self):
        return '<a class="btn btn-lg btn-primary btn-block col-8 offset-md-2" href="/login">Sign in with Azure Active Directory</a>'


entrypoint = (AADConfig, AADAuthProvider)
