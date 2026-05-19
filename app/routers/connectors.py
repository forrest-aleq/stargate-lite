"""
Connector status routes for Stargate Lite.
"""

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.database import CredentialManager
from app.logging_config import get_logger
from app.models import (
    ConnectedServicesRequest,
    ConnectedServicesResponse,
    ConnectorStatusRequest,
    ConnectorStatusResponse,
    WorkflowConnectorStatus,
)
from app.services.connector_health import (
    aggregate_connector_status,
    build_workflow_connector_statuses,
)

router = APIRouter(prefix="/api/v1", tags=["connectors"])
logger = get_logger(__name__)


def _normalize_services(services: list[str]) -> list[str]:
    """Normalize service names and dedupe while preserving order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in services:
        service = raw.strip().lower()
        if not service or service in seen:
            continue
        seen.add(service)
        normalized.append(service)
    return normalized


async def _load_workflow_statuses(
    org_id: str,
    user_id: str,
    services: list[str],
    now: datetime,
) -> list[WorkflowConnectorStatus]:
    credentials = await asyncio.to_thread(
        CredentialManager.get_credentials_for_org_user,
        org_id,
        user_id,
    )
    return build_workflow_connector_statuses(services, credentials, now)


@router.post("/connectors/status", response_model=ConnectorStatusResponse)
async def check_workflow_connector_status(
    request: ConnectorStatusRequest, _: bool = Depends(verify_api_key)
) -> ConnectorStatusResponse:
    """
    Check connector authentication status for specific services (workflow context).

    This endpoint is called by the workflow manifest builder to check which
    connectors are authenticated before presenting a workflow preview to the user.
    """
    services = _normalize_services(request.services)
    if not services:
        # Fail closed: empty service set should never imply "all connected".
        logger.warning(
            "connectors/status called with empty services list",
            org_id=request.org_id,
            user_id=request.user_id,
            log_event="connectors_empty_services",
        )
        return ConnectorStatusResponse(connectors=[], all_connected=False, missing_count=1)

    now = datetime.now(UTC)
    connectors = await _load_workflow_statuses(request.org_id, request.user_id, services, now)
    all_connected, missing_count = aggregate_connector_status(connectors)

    return ConnectorStatusResponse(
        connectors=connectors, all_connected=all_connected, missing_count=missing_count
    )


@router.post("/connectors/connected", response_model=ConnectedServicesResponse)
async def get_connected_services(
    request: ConnectedServicesRequest, _: bool = Depends(verify_api_key)
) -> ConnectedServicesResponse:
    """Return the lightweight live connector-truth surface for an org/user principal."""
    now = datetime.now(UTC)
    credentials = await asyncio.to_thread(
        CredentialManager.get_credentials_for_org_user,
        request.org_id,
        request.user_id,
    )
    services = sorted(
        {
            str(credential.get("service") or "").strip().lower()
            for credential in credentials
            if str(credential.get("service") or "").strip()
        }
    )
    statuses = build_workflow_connector_statuses(services, credentials, now)
    return ConnectedServicesResponse(
        connected_services=[status.kind for status in statuses if status.status == "connected"],
        expired_services=[status.kind for status in statuses if status.status == "expired"],
    )
