import os
from pathlib import Path
from typing import Any, Dict

from fastapi_aad_auth import Authenticator, Config
from fastapi_aad_auth.ui import UI as _UI
from fastapi_aad_auth.ui.jinja import Jinja2Templates
from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.responses import RedirectResponse

from docserver._copyright import get_copyright
from docserver.ui.context import get_base_context


templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


class AuthUI(_UI):

    def __init__(self, config: Config, authenticator: Authenticator, base_context: Dict[str, Any] = None):
        """Initialise the UI based on the provided configuration.

        Keyword Args:
            config (fastapi_aad_auth.config.Config): Authentication configuration (includes ui and routing, as well as AAD Application and Tenant IDs)
            authenticator (fastapi_aad_auth.auth.Authenticator): The authenticator object
            base_context (Dict[str, Any]): Add the authentication to the router
        """
        if base_context is None:
            base_context = {}
        global_base_context = get_base_context()
        global_base_context.update(base_context)


        super().__init__(config, authenticator, global_base_context)

        self.login_template_path = Path(self.config.login_ui.template_file)
        self.user_template_path = Path(self.config.login_ui.user_template_file)
        self.login_templates = Jinja2Templates(directory=str(self.login_template_path.parent))
        self.user_templates = Jinja2Templates(directory=str(self.user_template_path.parent))

    def _login(self, request: Request):
        if not self.config.enabled or self._authenticator.auth_backend.is_authenticated(request):
            # This is authenticated so go straight to the homepage
            return RedirectResponse('/')
        explanation = f'Built from <a href="https://github.com/djpugh/docserver">docserver</a> ({self._base_context["version"]})'
        return super()._login(request, copyright=get_copyright(), explanation=explanation)
