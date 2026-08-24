import logging
from app.db import models
from contextlib import asynccontextmanager
from app.api.routes.contracts import router as contracts_router
from app.api.routes.auth import router as auth_router
from fastapi import FastAPI
from app.api.routes.vendors import router as vendors_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.routes.jobs import router as jobs_router
from app.db.database import close_database, create_tables
from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.exception_handlers import (
    business_rule_handler,
    resource_conflict_handler,
    resource_not_found_handler,
)
from app.core.exceptions import ForbiddenError
from app.core.exception_handlers import forbidden_handler

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    logger.info("Starting application")

    await create_tables()

    logger.info("Database tables created")

    yield

    logger.info("Shutting down application")

    await close_database()

    logger.info("Database connection closed")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
app.include_router(contracts_router)
app.include_router(jobs_router)
app.include_router(auth_router)
app.include_router(vendors_router)
app.add_exception_handler(
    ResourceNotFoundError,
    resource_not_found_handler,
)
app.add_exception_handler(
    ResourceConflictError,
    resource_conflict_handler,
)
app.add_exception_handler(
    BusinessRuleError,
    business_rule_handler,
)
app.add_exception_handler(
    ForbiddenError,
    forbidden_handler,
)

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return application health status."""

    logger.info("Health check requested")

    return {"status": "ok"}