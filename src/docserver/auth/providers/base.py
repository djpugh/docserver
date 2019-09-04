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
        state = self.auth_state_klass.load_from_session(config.auth.serializer, request.session)
        return state.is_authenticated()

    def login(self, request):
        raise NotImplementedError

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
            state = self.auth_state_klass.load_from_session(config.auth.serializer, request.session, url=request.url)
            logger.debug(f'Authentication state {state} - Authenticated = {state.is_authenticated()}')
            return state.credentials, state.authenticated_user
        except Exception:
            logger.exception('Error authenticating')
        return None
