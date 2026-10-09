import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import ForbiddenError
from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


def log_http_error(request: Request, status_code: int, detail: object) -> None:
    """Write a consistent HTTP error record with method and path."""
    logger.warning(
        "HTTP %s | %s %s | detail=%s",
        status_code,
        request.method,
        request.url.path,
        detail,
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Log standard FastAPI errors such as 401 and 403."""
    log_http_error(request, exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Log malformed request payloads and return HTTP 422."""
    log_http_error(request, 422, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Log unexpected failures without exposing internal details."""
    logger.exception("Unhandled application error | %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})

async def forbidden_handler(
    request: Request,
    exc: ForbiddenError,
) -> JSONResponse:
    """Handle authorization failures."""

    log_http_error(request, 403, str(exc))

    return JSONResponse(
        status_code=403,
        content={
            "detail": str(exc),
        },
    )

async def resource_not_found_handler(
    request: Request,
    exc: ResourceNotFoundError,
) -> JSONResponse:
    """Handle resource-not-found errors."""

    log_http_error(request, 404, str(exc))

    return JSONResponse(
        status_code=404,
        content={
            "detail": str(exc),
        },
    )


async def resource_conflict_handler(
    request: Request,
    exc: ResourceConflictError,
) -> JSONResponse:
    """Handle resource-conflict errors."""

    log_http_error(request, 409, str(exc))

    return JSONResponse(
        status_code=409,
        content={
            "detail": str(exc),
        },
    )


async def business_rule_handler(
    request: Request,
    exc: BusinessRuleError,
) -> JSONResponse:
    """Handle business-rule violations."""

    log_http_error(request, 400, str(exc))

    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
        },
    )