from pathlib import Path

from fastapi_aad_auth import AuthenticationState, Authenticator as _Authenticator  # noqa: F401
from fastapi_aad_auth.errors import base_error_handler, ConfigurationError
from fastapi_aad_auth.ui.jinja import Jinja2Templates
from starlette.requests import Request
from starlette.responses import Response

from docserver.auth.providers.upload import UploadBearerProvider
from docserver.config import config
from docserver.ui.templates import nav


class Authenticator(_Authenticator):

    # TODO: add handler for non interactive auth error
    def _set_error_handlers(self, app):

        error_template_path = Path(self.config.login_ui.error_template_file)
        error_templates = Jinja2Templates(directory=str(error_template_path.parent))
        if self.config.login_ui.app_name:
            self._base_context['appname'] = self.config.login_ui.app_name
        else:
            self._base_context['appname'] = app.title
        self._base_context['static_path'] = self.config.login_ui.static_path

        @app.exception_handler(ConfigurationError)
        async def configuration_error_handler(request: Request, exc: ConfigurationError) -> Response:
            error_message = "Oops! It seems like the application has not been configured correctly, please contact an admin"
            error_type = 'Authentication Configuration Error'
            status_code = 500
            return base_error_handler(request, exc, error_type, error_message, error_templates, error_template_path, context=self._base_context.copy(), status_code=status_code)

    def get_api_token(self, scopes):
        upload_token_providers = [u for u in self._providers if isinstance(u, UploadBearerProvider)]
        if upload_token_providers:
            result = dict(zip(('access_token', 'expires_at'), upload_token_providers[0].get_token(scopes)))
        else:
            result = {'access_token': None, 'expires_at': None}
        self.logger.debug(result)
        return result


authenticator = Authenticator(config.auth, base_context={'logo': config.logo, 'nav': nav.nav(config.logo)})
