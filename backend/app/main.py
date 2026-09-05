"""
Smart Farmer backend — FastAPI application foundation.

This file wires together configuration, logging, CORS, middleware,
exception handling, and versioned routing. No business logic lives here.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging, get_logger
from app.middleware.error_handling import register_exception_handlers
from app.middleware.request_logging import RequestLoggingMiddleware
from app.services.scheduler import shutdown_scheduler, start_scheduler

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(level="DEBUG" if settings.environment == "development" else "INFO")
    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    start_scheduler(settings)
    yield
    shutdown_scheduler()
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Smart Farmer API",
        version="0.1.0",
        description=(
            "Foundation build. Business modules (farmer/farm/crop, disease "
            "diagnosis, weather, marketplace, expert workflow, payments) are "
            "not yet implemented — see PROJECT_STATUS.md."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_origin_regex=settings.cors_allowed_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
