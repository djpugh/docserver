import logging
import os
import typing

from starlette.responses import Response, PlainTextResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from docserver.auth.permissions.compare import get_permissions
from docserver.db.models import Package


logger = logging.getLogger(__name__)


class PermissionsCheck:
    def is_authorised(self, provided_permissions, path):
        return True


class DBPermissionsCheck(PermissionsCheck):

    def __init__(self, session_maker):
        self.session_maker = session_maker

    def is_authorised(self, provided_permissions, path):
        logger.debug(f'Checking {path}')
        name = os.path.split(path)[0]
        logger.debug(f'Module name: {name}')
        logger.debug(f'Provided permissions: {provided_permissions}')
        packages = Package.read_unique(self.session_maker(), params={'name': name})
        if packages.is_authorised('read', provided_permissions):
            return True
        else:
            return False


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
        provided_permissions = get_permissions(scope)
        if not self.permissions_check.is_authorised(provided_permissions, path):
            return PlainTextResponse("Unauthorised", status_code=405)
        return await super().get_response(path, scope)
