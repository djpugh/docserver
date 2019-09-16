from datetime import datetime, timedelta
import logging
from typing import List

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
import jwt
from starlette.requests import Request
from starlette.authentication import AuthenticationBackend, AuthCredentials, UnauthenticatedUser

from docserver.auth.state import AuthState, APIUser, AuthenticationOptions
from docserver.config import config


logger = logging.getLogger(__name__)


class APIAuthenticationCredentials(HTTPAuthorizationCredentials):
    permissions: List[str]


class APIAuthenticator(HTTPBearer):

    async def __call__(self, request: Request):
        credentials = await super().__call__(request)
        if config.auth.enabled:
            logger.info(f'Authenticating {request}')
            state = config.auth.provider_object.authenticate_token(credentials.credentials)
            logger.info(state)
            if state.is_authenticated():
                scopes = state.credentials.scopes
            else:
                logger.info(f'Not authenticated for {request}')
                raise PermissionError('Not Authenticated')
        else:
            scopes = [config.permissions.default_read_permission]
        credentials = APIAuthenticationCredentials(scheme=credentials.scheme,
                                                   credentials=credentials.credentials,
                                                   permissions=scopes)
        return credentials


class BaseAuthenticationProvider(AuthenticationBackend):

    def __init__(self, *args, **kwargs):
        self.auth_state_klass = kwargs.get('auth_state_klass', AuthState)

    def process_login_callback(self, request):
        redirect = request.query_params.get('redirect', '/')
        auth_state = self.auth_state_klass(login_redirect=redirect)
        auth_state.save_to_session(config.auth.serializer, request.session)
        return auth_state

    def check_state(self, request):
        state = self.auth_state_klass.load_from_session(config.auth.serializer, request.session)
        return state.is_authenticated()

    def login(self, request):
        raise NotImplementedError

    def get_token(self, request):
        raise NotImplementedError

    def validate_token(self, token):
        raise NotImplementedError

    def authenticate_token(self, token, auth_state=None):
        # Here we are going to try authenticating to the scope (graph) with a token and getting the user response
        if not auth_state:
            auth_state = self.auth_state_klass()
        logger.info(f'Getting Auth state: {auth_state}')
        try:
            if isinstance(token, str):
                token = token.encode()
            token = jwt.decode(token, str(config.auth.token_secret))
            logger.info(token)
            scopes = token['scopes']
        except Exception:
            logger.exception('Error handling token')
            raise PermissionError('Unauthorised')
        auth_state.user = APIUser(permissions=scopes)
        auth_state.state = AuthenticationOptions.authenticated
        logger.info(f'JWT Auth state: {auth_state}')

        return auth_state

    def load_from_headers(self, headers):
        # We have a token, so this is then
        auth = headers.get('Authorization', None)
        if auth:
            return self.authenticate_token(get_authorization_scheme_param(auth)[1])
        return None

    @property
    def login_html(self):
        raise NotImplementedError

    def logout(self, request):
        self.auth_state_klass.logout(config.auth.serializer, request.session)

    async def authenticate(self, request: Request, *args, **kwargs):
        state = self.is_authenticated(request)
        logger.debug(f'Provided authentication state {state}')
        return state

    def is_authenticated(self, request):
        logger.debug(f'Authenticating {request}')
        try:
            state = self.auth_state_klass.load_from_session(config.auth.serializer, request.session, url=request.url,)
            logger.debug(f'Authentication state {state} - Authenticated = {state.is_authenticated()}, redirect url = {state.redirect}')
            if not state.is_authenticated():
                # Lets try to load the state from the headers
                logger.info('Checking headers for token')
                state = self.load_from_headers(request.headers)
            return state.credentials, state.authenticated_user
        except Exception:
            logger.exception('Error authenticating')
        return None

    def get_api_token(self, scopes=None):
        if not scopes:
            scopes = [config.permissions.default_write_permission]
        expires = datetime.utcnow() + timedelta(seconds=config.auth.token_lifetime)
        token = jwt.encode({'scopes': scopes, 'exp': expires}, str(config.auth.token_secret))
        return token
