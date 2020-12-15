import logging
import os
import typing

from fastapi_aad_auth._base.state import AuthenticationError, AuthenticationOptions
from starlette.responses import PlainTextResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from docserver.db.models import Package
from docserver.permissions.get import get_permissions_from_request


logger = logging.getLogger(__name__)


class PermissionsCheck:
    def is_authorised(self, provided_permissions, path):
        return AuthenticationOptions.authenticated


class LoggedInPermissionsCheck(PermissionsCheck):

    def is_authorised(self, provided_permissions, path):
        logger.debug(f'Provided permissions: {provided_permissions}')
        if 'authenticated' in provided_permissions:
            return AuthenticationOptions.authenticated
        else:
            return AuthenticationOptions.unauthenticated


class DBPermissionsCheck(LoggedInPermissionsCheck):

    def __init__(self, session_maker):
        self.session_maker = session_maker

    def is_authorised(self, provided_permissions, path):
        result = super().is_authorised(provided_permissions, path)
        if result == AuthenticationOptions.unauthenticated:
            return result
        logger.debug(f'Checking {path}')
        name = os.path.normpath(path).split(os.path.sep)[0]
        logger.debug(f'Module name: {name}')
        logger.debug(f'Provided permissions: {provided_permissions}')
        package = Package.read_unique(params={'name': name}, db=self.session_maker())
        if package and package.is_authorised('read', provided_permissions):
            return AuthenticationOptions.authenticated
        else:
            return AuthenticationOptions.not_allowed


class PermissionedStaticFiles(StaticFiles):
    def __init__(
        self,
        *,
        permissions_check: typing.Union[dict, PermissionsCheck],
        directory: str = None,
        packages: typing.List[str] = None,
        html: bool = False,
        check_dir: bool = True,
    ) -> None:
        super().__init__(directory=directory, packages=packages, html=html, check_dir=check_dir)
        self.permissions_check = permissions_check

    async def get_response(self, path: str, scope: Scope) -> Response:
        """
        Returns an HTTP response, given the incoming path, method and request headers.
        """
        provided_permissions = get_permissions_from_request(scope)
        result = self.permissions_check.is_authorised(provided_permissions, path)
        if result == AuthenticationOptions.not_allowed:
            return PlainTextResponse("Unauthorised", status_code=405)
        elif result == AuthenticationOptions.unauthenticated:
            raise AuthenticationError('Login Required', scope['root_path'])
        return await super().get_response(path, scope)
