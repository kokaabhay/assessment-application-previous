from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import ForbiddenError
from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)

async def forbidden_handler(
    request: Request,
    exc: ForbiddenError,
) -> JSONResponse:
    """Handle authorization failures."""

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

    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
        },
    )