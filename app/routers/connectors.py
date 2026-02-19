"""
Connector status routes for Stargate Lite.
"""

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.logging_config import get_logger
from app.models import ConnectorStatusRequest, ConnectorStatusResponse
from app.services.connector_health import (
    aggregate_connector_status,
    build_workflow_connector_status,
)

router = APIRouter(prefix="/api/v1", tags=["connectors"])
logger = get_logger(__name__)


@router.post("/connectors/status", response_model=ConnectorStatusResponse)
async def check_workflow_connector_status(
    request: ConnectorStatusRequest, _: bool = Depends(verify_api_key)
) -> ConnectorStatusResponse:
    """
    Check connector authentication status for specific services (workflow context).

    This endpoint is called by the workflow manifest builder to check which
    connectors are authenticated before presenting a workflow preview to the user.
    """
    if not request.services:
        # Fail closed: empty service set should never imply "all connected".
        logger.warning(
            "connectors/status called with empty services list",
            org_id=request.org_id,
            user_id=request.user_id,
            log_event="connectors_empty_services",
        )
        return ConnectorStatusResponse(connectors=[], all_connected=False, missing_count=1)

    now = datetime.now(UTC)
    connectors = list(
        await asyncio.gather(
            *[
                asyncio.to_thread(
                    build_workflow_connector_status, service, request.org_id, request.user_id, now
                )
                for service in request.services
            ]
        )
    )
    all_connected, missing_count = aggregate_connector_status(connectors)

    return ConnectorStatusResponse(
        connectors=connectors, all_connected=all_connected, missing_count=missing_count
    )
