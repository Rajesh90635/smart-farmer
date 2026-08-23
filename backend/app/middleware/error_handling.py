"""
Global exception handling. Every error response — validation, a deliberate
AppError, a raised HTTPException (401/403/404/etc.), or a genuine unhandled
bug — comes out in the same JSON shape (see docs/API_CONVENTIONS.md):

    {"error": {"code": "...", "message": "...", "correlation_id": "...", "details": ...?}}

Internal exception detail is never included for unhandled exceptions —
only a correlation id, so the real detail is findable in server logs.
"""
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import error_codes
from app.core.errors import AppError
from app.core.logging_config import get_logger

logger = get_logger("errors")

_CODE_BY_STATUS = {
    401: error_codes.UNAUTHORIZED,
    403: error_codes.FORBIDDEN,
    404: error_codes.NOT_FOUND,
    429: error_codes.RATE_LIMITED,
}


def _error_body(code: str, message: str, correlation_id: str, details: object | None = None) -> dict:
    body: dict = {"error": {"code": code, "message": message, "correlation_id": correlation_id}}
    if details is not None:
        body["error"]["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        correlation_id = getattr(request.state, "correlation_id", "-")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, correlation_id),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        correlation_id = getattr(request.state, "correlation_id", "-")
        code = _CODE_BY_STATUS.get(exc.status_code, "ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code, str(exc.detail), correlation_id),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        correlation_id = getattr(request.state, "correlation_id", "-")
        # Pydantic v2's error dicts can include a raw exception instance
        # under ctx.error (e.g. from a @field_validator raising ValueError)
        # which json.dumps can't serialize on its own - jsonable_encoder
        # converts it (and anything else non-JSON-native) to a plain value.
        safe_details = jsonable_encoder(exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(error_codes.VALIDATION_ERROR, "Request validation failed.", correlation_id, safe_details),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        correlation_id = getattr(request.state, "correlation_id", "-")
        logger.error("Unhandled exception: %s", exc, extra={"correlation_id": correlation_id}, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred.", correlation_id),
        )
