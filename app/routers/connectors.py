"""
Connector status routes for Stargate Lite.
"""

from collections.abc import Callable
from datetime import datetime

from fastapi import APIRouter, Depends

from app.models import ConnectorStatusRequest, ConnectorStatusResponse
from app.services.connector_health import (
    aggregate_connector_status,
    build_workflow_connector_status,
)

router = APIRouter(prefix="/api/v1", tags=["connectors"])


def _get_api_key_verifier() -> Callable[..., bool]:
    """Import verify_api_key lazily to avoid circular imports."""
    from app.main import verify_api_key

    return verify_api_key


@router.post("/connectors/status", response_model=ConnectorStatusResponse)
async def check_workflow_connector_status(
    request: ConnectorStatusRequest, _: bool = Depends(_get_api_key_verifier())
) -> ConnectorStatusResponse:
    """
    Check connector authentication status for specific services (workflow context).

    This endpoint is called by the workflow manifest builder to check which
    connectors are authenticated before presenting a workflow preview to the user.
    """
    now = datetime.utcnow()
    connectors = [
        build_workflow_connector_status(service, request.org_id, request.user_id, now)
        for service in request.services
    ]
    all_connected, missing_count = aggregate_connector_status(connectors)

    return ConnectorStatusResponse(
        connectors=connectors, all_connected=all_connected, missing_count=missing_count
    )
