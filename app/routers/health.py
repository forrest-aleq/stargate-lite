"""
Health check routes for Stargate Lite.
"""

import os
from datetime import datetime

from fastapi import APIRouter

from app.constants.services import ALL_SERVICES_OAUTH
from app.database import CredentialManager
from app.models import ConnectorHealthResponse, HealthResponse
from app.observability import increment_metric
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
    """Health check endpoint"""
    import logging

    logger = logging.getLogger("stargate-lite")

    # Send custom metric to DataDog (environment and service tags added automatically)
    increment_metric("stargate_lite.health_check.called")

    # Log will be automatically correlated with trace by ddtrace
    logger.info("Health check called - all services healthy")

    return HealthResponse(
        status="healthy",
        version=_get_version(),
        capabilities_count=len(CAPABILITY_REGISTRY),
        services={
            "quickbooks": "ok",
            "stripe": "ok",
            "hubspot": "ok",
            "google": "ok",
            "slack": "ok",
        },
    )


@router.get("/health/connectors", response_model=ConnectorHealthResponse)
async def connector_health_check() -> ConnectorHealthResponse:
    """
    Detailed health check for all connectors
    Shows credential status, expiry, and connection counts per service
    """
    all_credentials = CredentialManager.get_all_credentials()
    service_data = group_credentials_by_service(all_credentials)
    now = datetime.utcnow()

    connectors = [
        build_connector_status(service, requires_oauth, service_data[service]["connections"], now)
        for service, requires_oauth in ALL_SERVICES_OAUTH.items()
    ]
    connectors.sort(key=lambda x: x.service)

    return ConnectorHealthResponse(
        status="operational",
        version=_get_version(),
        total_connectors=len(ALL_SERVICES_OAUTH),
        total_connections=len(all_credentials),
        connectors=connectors,
    )
