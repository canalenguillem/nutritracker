import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.schemas.errors import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unknown"))


def _error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
) -> JSONResponse:
    response = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details,
            request_id=_request_id(request),
        )
    )
    return JSONResponse(status_code=status_code, content=jsonable_encoder(response))


async def validation_error_handler(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    return _error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="The request data is invalid.",
        details=jsonable_encoder(exception.errors()),
    )


async def http_error_handler(request: Request, exception: HTTPException) -> JSONResponse:
    code_by_status = {
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "RESOURCE_NOT_FOUND",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
    }
    message = exception.detail if isinstance(exception.detail, str) else "The request failed."
    return _error_response(
        request=request,
        status_code=exception.status_code,
        code=code_by_status.get(exception.status_code, "HTTP_ERROR"),
        message=message,
    )


async def unexpected_error_handler(request: Request, exception: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_request_error",
        extra={
            "request_id": _request_id(request),
            "error_type": type(exception).__name__,
        },
    )
    return _error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
    )


def register_error_handlers(application: FastAPI) -> None:
    application.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(HTTPException, http_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(Exception, unexpected_error_handler)
