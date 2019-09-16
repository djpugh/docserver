from json import JSONDecodeError
import logging
import os
from pathlib import Path
from typing import List, Optional

from fastapi.security.http import HTTPBearer
import msal
from pydantic import UrlStr, Schema, SecretStr, validator
import requests
from starlette.authentication import AuthenticationError
from starlette.responses import RedirectResponse

from docserver.auth.providers.base import BaseAuthenticationProvider
from docserver.auth.providers.config import ProviderConfig
from docserver.auth.state import AuthenticationOptions, AuthState, User
from docserver.config import config
from docserver.db import models as db_models

logger = logging.getLogger(__name__)


MS_GRAPH_API_USER = "https://graph.microsoft.com/v1.0/me"


class AADAuth(AuthState):

    def set_user_from_response(self, graph_user):
        # {'@odata.context': 'https://graph.microsoft.com/v1.0/$metadata#users/$entity',
        #  'businessPhones': [],
        #  'displayName': '...',
        #  'givenName': '...',
        #  'jobTitle': '...',
        #  'mail': '...',
        #  'mobilePhone': None,
        #  'officeLocation': '...',
        #  'preferredLanguage': None,
        #  'surname': '...',
        #  'userPrincipalName': '...',
        #  'id': '...'}
        name = ' '.join([graph_user['givenName'], graph_user['surname']])
        email = graph_user['mail'].lower()
        username = graph_user['userPrincipalName']
        # roles = graph_user['id_token_claims'].get('app_roles', [])
        user = User(name=name, email=email, username=username, roles=[])
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

    def get_token(self, request):
        auth_state = self.auth_state_klass.load_from_session(config.auth.serializer, request.session)
        if auth_state.is_authenticated():
            account = self.msal_application.get_accounts(auth_state.user.email)[0]
            return self.msal_application.acquire_token_silent(scopes=config.auth.provider.scope, account=account,
                                                              authority=config.auth.provider.authority,)
        else:
            raise AuthenticationError('Not authenticated')

    def validate_token(self, token):
        # Here we are going to try authenticating to the scope (graph) with a token and getting the user response
        try:
            return 'mail' in self.get_user(token)
        except JSONDecodeError:
            return False

    def authenticate_token(self, token, auth_state=None):
        # Here we are going to try authenticating to the scope (graph) with a token and getting the user response
        if not auth_state:
            auth_state = self.auth_state_klass()
        try:
            user = self.get_user(token)
            auth_state.set_user_from_response(user)
        except (JSONDecodeError, KeyError):
            logger.info('AAD auth failed, falling back to JWT')
            auth_state = super().authenticate_token(token, auth_state)
        return auth_state

    @staticmethod
    def get_user(token):
        s = requests.sessions.Session()
        s.headers['Authorization'] = f'Bearer {token}'
        return s.get(MS_GRAPH_API_USER).json()

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
        if not 'access_token' in result:
            raise ValueError(f'Error connecting to AAD {result}')
        user = self.get_user(result['access_token'])
        auth_state.set_user_from_response(user)
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

    @property
    def api_auth_scheme_klass(self):
        return HTTPBearer

    def process_api_form(self, request, form):
        if form.token and self.validate_token(form.token):
            return form.token
        else:
            return self.get_token(request)


entrypoint = (AADConfig, AADAuthProvider)
