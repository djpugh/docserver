import os
from pathlib import Path
from typing import Any, Dict

from fastapi_aad_auth.ui import UI as _UI
from pkg_resources import resource_filename
from starlette.requests import Request
from starlette.responses import RedirectResponse

from docserver import __copyright__, __version__, auth, config
from docserver.ui.jinja import Jinja2Templates

templates = Jinja2Templates(directory=os.path.dirname(resource_filename('docserver.ui.templates', 'index.html')))


class AuthUI(_UI):

    def __init__(self, config: 'config.Config', authenticator: 'auth.Authenticator', base_context: Dict[str, Any] = None):
        """Initialise the UI based on the provided configuration.

        Keyword Args:
            config (fastapi_aad_auth.config.Config): Authentication configuration (includes ui and routing, as well as AAD Application and Tenant IDs)
            authenticator (fastapi_aad_auth.auth.Authenticator): The authenticator object
            base_context (Dict[str, Any]): Add the authentication to the router
        """
        super().__init__(config, authenticator, base_context)
        self.login_template_path = Path(self.config.login_ui.template_file)
        self.user_template_path = Path(self.config.login_ui.user_template_file)
        self.login_templates = Jinja2Templates(directory=str(self.login_template_path.parent))
        self.user_templates = Jinja2Templates(directory=str(self.user_template_path.parent))

    def _login(self, request: Request):
        if not config.auth.enabled or config.auth.provider_object.check_state(request):
            # This is authenticated so go straight to the homepage
            return RedirectResponse('/')
        return super()._login(app_name=self.config.app_name,
                              copyright=__copyright__,
                              version=__version__,
                              logo='<span class="oi oi-book splash-logo mb-4" title="Docserver" aria-hidden="true"></span>')
