from starlette.requests import Request
from starlette.authentication import AuthenticationBackend, AuthenticationError

from docserver.auth.state import AuthState


class BaseAuthenticationProvider(AuthenticationBackend):

    def __init__(self, config, *args, **kwargs):
        self.config = config
        self.auth_state_klass = kwargs.get('auth_state_klass', AuthState)

    def process_login_request(self, request):
        redirect = request.query_params.get('redirect', '/')
        auth_state = self.auth_state_klass(login_redirect=redirect)
        request.session['auth'] = auth_state.store(self.config.serializer)
        return auth_state

    def check_state(self, request):
        return AuthState.is_authenticated(request.session)

    def login(self, request):
        raise NotImplementedError

    async def authenticate(self, request: Request, *args, **kwargs):
        state = AuthState.load_from_session(self.config.serializer, request.session)
        if state.is_authenticated():
            # We are authenticated so get the parameters
            return state.credentials, state.authenticated_user
        else:
            raise AuthenticationError('Not Authenticated')
