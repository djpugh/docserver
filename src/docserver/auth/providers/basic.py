import logging


from starlette.authentication import SimpleUser, AuthCredentials

from docserver.auth.providers.base import BaseAuthenticationProvider
from docserver.auth.providers.config import ProviderConfig


logger = logging.getLogger(__name__)


class BasicConfig(ProviderConfig):
    pass


class BasicAuthProvider(BaseAuthenticationProvider):

    pass
    #
    # async def authenticate(self, request):
    #     if "Authorization" not in request.headers:
    #         return
    #
    #     auth = request.headers["Authorization"]
    #     try:
    #         scheme, credentials = auth.split()
    #         if scheme.lower() != 'basic':
    #             return
    #         decoded = base64.b64decode(credentials).decode("ascii")
    #     except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
    #         raise AuthenticationError('Invalid basic auth credentials')
    #
    #     username, _, password = decoded.partition(":")
    #     # TODO: You'd want to verify the username and password here,
    #     #       possibly by installing `DatabaseMiddleware`
    #     #       and retrieving user information from `request.database`.
    #     return AuthCredentials(["authenticated"]), SimpleUser(username)


entrypoint = (BasicConfig, BasicAuthProvider)
