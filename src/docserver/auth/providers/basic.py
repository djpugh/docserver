import logging


from docserver.auth.providers.base import BaseAuthenticationProvider
from docserver.auth.providers.config import ProviderConfig


logger = logging.getLogger(__name__)


class BasicConfig(ProviderConfig):
    pass


class BasicAuthProvider(BaseAuthenticationProvider):

    pass
    # TODO implement from fastapi example


entrypoint = (BasicConfig, BasicAuthProvider)
