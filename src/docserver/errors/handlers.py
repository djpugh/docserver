import logging
import urllib.parse

from fastapi.exceptions import RequestValidationError
from starlette.authentication import AuthenticationError
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.status import HTTP_403_FORBIDDEN, HTTP_422_UNPROCESSABLE_ENTITY


logger = logging.getLogger(__name__)


def register(app, handler=None, exception=None):
    """Default to registering all handlers here"""
    if handler is None:
        for handler, exception in ALL_HANDLERS:
            app.exception_handler(exception)(handler)
    else:
        return app.exception_handler(exception)(handler)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    try:
        logger.error(f'Error handling Request Validation Error: {exc.errors()} - request: {request.headers}')
        return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})
    except RuntimeError:
        try:
            exc_str = str(exc)
        except RuntimeError as e:
            exc_str = str(e)
        logger.exception(f'Error handling Request Validation Error {exc_str} - request: {request.headers}')
        return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})


async def authentication_exception_handler(request: Request, exc: AuthenticationError) -> RedirectResponse:
    return RedirectResponse(f'/splash?error={urllib.parse.quote(exc[0])}')


async def permission_exception_handler(request: Request, exc: PermissionError) -> JSONResponse:
    return JSONResponse(status_code=HTTP_403_FORBIDDEN, content={"detail": "Unauthorised"})


ALL_HANDLERS = [(validation_exception_handler, RequestValidationError),
                (authentication_exception_handler, AuthenticationError),
                (permission_exception_handler, PermissionError)]
