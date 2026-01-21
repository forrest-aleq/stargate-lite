"""
Stargate Lite - Main Application
The "Hands" of the Aleq MIND
"""

import os

from datadog import statsd

# DataDog APM - import and patch early
from ddtrace import patch_all
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Patch all supported libraries for automatic instrumentation (includes logging)
patch_all(logging=True)

from app.database import init_db
from app.logging_config import get_logger
from app.observability import setup_logging
from app.routers import connectors, credentials, execute, health, schemas
from app.routers.oauth import router as oauth_router
from app.sentry_config import init_sentry

# Initialize structured logger
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Stargate Lite",
    description="Execution Layer ('The Hands') for Aleq MIND",
    version="1.0.0",
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
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
)

# Include routers
app.include_router(health.router)
app.include_router(connectors.router)
app.include_router(credentials.router)
app.include_router(execute.router)
app.include_router(oauth_router)
app.include_router(schemas.router)

# Configure DogStatsD client for custom metrics
statsd.host = os.getenv("DD_AGENT_HOST", "localhost")
statsd.port = int(os.getenv("DD_DOGSTATSD_PORT", "8125"))

# Re-export verify_api_key for backwards compatibility (now lives in app.auth)
from app.auth import verify_api_key  # noqa: F401


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database, logging, and error tracking on startup"""
    # Initialize Sentry first to catch any startup errors
    sentry_enabled = init_sentry()

    init_db()
    setup_logging()  # Configure file logging AFTER uvicorn starts

    logger.info(
        "Stargate Lite is ready to execute!",
        sentry_enabled=sentry_enabled,
        log_event="startup_complete",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8001)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
