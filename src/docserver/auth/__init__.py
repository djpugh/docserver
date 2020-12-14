from fastapi_aad_auth import AuthenticationState, Authenticator  # noqa: F401

from docserver.config import config

authenticator = Authenticator(config.auth)
