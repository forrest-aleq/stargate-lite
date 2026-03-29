"""
Stargate Lite - Main Application
The "Hands" of the Aleq MIND
"""

import os

from app.env import load_env_files

# Load local env files before any os.getenv reads.
load_env_files()

# Version - Single source of truth
# Update this on every release (see RELEASE_GUIDE.md)
VERSION = "0.11.0"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# DataDog APM - only patch if DD_TRACE_ENABLED is not explicitly disabled
# This must happen before other imports to ensure proper instrumentation
if os.getenv("DD_TRACE_ENABLED", "true").lower() != "false":
    from datadog import statsd
    from ddtrace import patch_all

    # Patch all supported libraries for automatic instrumentation (includes logging)
    patch_all(logging=True)

    # Configure DogStatsD client for custom metrics
    statsd.host = os.getenv("DD_AGENT_HOST", "localhost")
    statsd.port = int(os.getenv("DD_DOGSTATSD_PORT", "8125"))

from app.custom_openapi import custom_openapi
from app.database import init_db
from app.logging_config import get_logger
from app.observability import setup_logging
from app.posthog_client import init_posthog
from app.routers import connectors, credentials, execute, health, schemas
from app.routers.oauth import router as oauth_router
from app.sentry_config import init_sentry

# Initialize structured logger
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Stargate Lite",
    description="Execution Layer ('The Hands') for Aleq MIND",
    version=VERSION,
)

# CORS middleware
# CORS configuration - restrict origins in production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8001").split(
    ","
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-API-Key",
        "X-Request-ID",
        "X-Session-ID",
        "X-Timestamp",
        "X-Signature-256",
    ],
)

# Include routers
app.include_router(health.router)
app.include_router(connectors.router)
app.include_router(credentials.router)
app.include_router(execute.router)
app.include_router(oauth_router)
app.include_router(schemas.router)

# Webhook receivers (inbound events from external services → Baby MARS)
from app.routers.webhooks import router as webhooks_router

app.include_router(webhooks_router)

# Override OpenAPI schema so runtime /openapi.json serves oneOf + discriminator
# (not anyOf) for the execute endpoint. This ensures deployed and generated specs match.
app.openapi = lambda: custom_openapi(app)  # type: ignore[method-assign]

# Re-export verify_api_key for backwards compatibility (now lives in app.auth)
from app.auth import verify_api_key  # noqa: F401


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database, logging, analytics, and error tracking on startup"""
    # Initialize Sentry first to catch any startup errors
    sentry_enabled = init_sentry()

    # Initialize PostHog for analytics
    posthog_enabled = init_posthog()

    init_db()
    setup_logging()  # Configure file logging AFTER uvicorn starts

    logger.info(
        "Stargate Lite is ready to execute!",
        sentry_enabled=sentry_enabled,
        posthog_enabled=posthog_enabled,
        log_event="startup_complete",
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Flush analytics and close connections on shutdown."""
    from app.database import engine
    from app.http_client import http_client
    from app.posthog_client import flush as posthog_flush
    from app.redis_client import redis_client

    posthog_flush()
    if redis_client._redis_client:
        redis_client._redis_client.close()
    http_client.session.close()
    engine.dispose()
    logger.info("Graceful shutdown complete", log_event="shutdown_complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),  # nosec B104 - intentional for containers
        port=int(os.getenv("PORT", 8001)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
