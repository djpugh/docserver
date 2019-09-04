from starlette.authentication import requires as starlette_requires

from docserver.config import config


def auth_required(fn):
    if config.auth.enabled:
        redirect = 'splash'
        scopes = 'authenticated'
        # This needs to be provided in the AuthCredentials object
        return starlette_requires(scopes, redirect=redirect)(fn)
    else:
        return fn
