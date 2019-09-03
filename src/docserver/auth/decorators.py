from starlette.authentication import requires as starlette_requires

from docserver.config import config


def requires(*args, **kwargs):
    if config.auth.enabled:
        print('auth enabled')
        kwargs['redirect'] = kwargs.get('redirect', '/login')
        return starlette_requires(*args, **kwargs)
    else:
        def wrapper(fn):
            return fn

        return wrapper
