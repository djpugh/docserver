import logging

from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


logger = logging.getLogger(__name__)


def register(app, handler=None, exception=None):
    """Default to registering all handlers here"""
    if handler is None:
        for exception, handler in ALL_HANDLERS:
            app.exception_handler(exception)(handler)
    else:
        return app.exception_handler(exception)(handler)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    try:
        return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})
    except RuntimeError:
        logger.exception(f'Error handling Request Validation Error {exc} - request: {request.headers} {request.body()}')
        return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})


ALL_HANDLERS = [(validation_exception_handler, RequestValidationError)]