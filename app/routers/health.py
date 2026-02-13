"""
Health check routes for Stargate Lite.
"""

import asyncio
import os
from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.constants.services import ALL_SERVICES_OAUTH, ENABLED_SERVICES
from app.database import CredentialManager, engine
from app.models import ConnectorHealthResponse, HealthResponse
from app.observability import increment_metric
from app.redis_client import redis_client
from app.registry import CAPABILITY_REGISTRY
from app.services.connector_health import (
    build_connector_status,
    group_credentials_by_service,
)


# Import version from main (avoid circular import by importing at module level)
def _get_version() -> str:
    from app.main import VERSION

    return VERSION


router = APIRouter(tags=["health"])


@router.get("/", response_model=HealthResponse)
async def root() -> HealthResponse:
    """Root endpoint - health check"""
    return HealthResponse(
        status="operational",
        version=_get_version(),
        capabilities_count=len(CAPABILITY_REGISTRY),
        services={
            "quickbooks": ("configured" if os.getenv("QUICKBOOKS_CLIENT_ID") else "not_configured"),
            "stripe": ("configured" if os.getenv("STRIPE_SECRET_KEY") else "not_configured"),
            "hubspot": ("configured" if os.getenv("HUBSPOT_CLIENT_ID") else "not_configured"),
            "google": ("configured" if os.getenv("GOOGLE_CLIENT_ID") else "not_configured"),
            "slack": ("configured" if os.getenv("SLACK_CLIENT_ID") else "not_configured"),
        },
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with real DB and Redis pings."""
    import logging

    logger = logging.getLogger("stargate-lite")

    increment_metric("stargate_lite.health_check.called")

    services: dict[str, str] = {}
    overall_healthy = True

    # Redis ping
    try:
        if redis_client._redis_client:
            await asyncio.to_thread(redis_client._redis_client.ping)
            services["redis"] = "connected"
        else:
            services["redis"] = "unavailable"
            overall_healthy = False
    except Exception:
        services["redis"] = "unavailable"
        overall_healthy = False

    # DB ping
    try:

        def _check_db() -> None:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        await asyncio.to_thread(_check_db)
        services["database"] = "connected"
    except Exception:
        services["database"] = "unavailable"
        overall_healthy = False

    status = "healthy" if overall_healthy else "degraded"
    logger.info(f"Health check called - status={status}")

    return HealthResponse(
        status=status,
        version=_get_version(),
        capabilities_count=len(CAPABILITY_REGISTRY),
        services=services,
    )


@router.get("/health/connectors", response_model=ConnectorHealthResponse)
async def connector_health_check() -> ConnectorHealthResponse:
    """
    Detailed health check for all connectors
    Shows credential status, expiry, and connection counts per service
    """
    all_credentials = await asyncio.to_thread(CredentialManager.get_all_credentials)
    service_data = group_credentials_by_service(all_credentials)
    now = datetime.now(UTC)

    enabled_services = {
        service: requires_oauth
        for service, requires_oauth in ALL_SERVICES_OAUTH.items()
        if service in ENABLED_SERVICES
    }

    connectors = [
        build_connector_status(service, requires_oauth, service_data[service]["connections"], now)
        for service, requires_oauth in enabled_services.items()
    ]
    connectors.sort(key=lambda x: x.service)

    return ConnectorHealthResponse(
        status="operational",
        version=_get_version(),
        total_connectors=len(enabled_services),
        total_connections=len(all_credentials),
        connectors=connectors,
    )
