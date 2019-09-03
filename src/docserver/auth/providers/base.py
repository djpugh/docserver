import logging

from starlette.requests import Request
from starlette.authentication import AuthenticationBackend, AuthCredentials, UnauthenticatedUser

from docserver.auth.state import AuthState
from docserver.config import config


logger = logging.getLogger(__name__)


class BaseAuthenticationProvider(AuthenticationBackend):

    def __init__(self, *args, **kwargs):
        self.auth_state_klass = kwargs.get('auth_state_klass', AuthState)

    def process_login_callback(self, request):
        redirect = request.query_params.get('redirect', '/')
        auth_state = self.auth_state_klass(login_redirect=redirect)
        auth_state.save_to_session(config.auth.serializer, request.session)
        return auth_state

    def check_state(self, request):
        return AuthState.is_authenticated(request.session)

    def login(self, request):
        raise NotImplementedError

    async def authenticate(self, request: Request, *args, **kwargs):
        return self.is_authenticated(request)

    def is_authenticated(self, request):
        print('Authenticating')
        try:
            print(request)
            print('REQ URL', request.url)
            state = AuthState.load_from_session(config.auth.serializer, request.session, url=request.url)
            print('state', state)
            print('Auth Complete')
            return state.credentials, state.authenticated_user
        except Exception:
            logger.exception('Error authenticating')
        return None
