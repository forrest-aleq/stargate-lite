"""
Connector health service - Helper functions for analyzing connector/credential status.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any

from app.constants.services import (
    ALL_SERVICES_OAUTH,
    SERVICE_DISPLAY_NAMES,
    WORKFLOW_OAUTH_REQUIREMENTS,
)
from app.database import CredentialManager
from app.models import ConnectorStatus, WorkflowConnectorStatus


def group_credentials_by_service(credentials: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group credentials by service name."""
    service_data: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"connections": [], "requires_oauth": False}
    )
    for cred in credentials:
        service = cred["service"]
        service_data[service]["connections"].append(cred)
        service_data[service]["requires_oauth"] = ALL_SERVICES_OAUTH.get(service, False)
    return service_data


def analyze_connections(
    connections: list[dict[str, Any]], now: datetime
) -> tuple[int, datetime | None, datetime | None]:
    """Analyze connections to find expired count, latest expiry, and latest updated."""
    expired_count = 0
    latest_expiry: datetime | None = None
    latest_updated: datetime | None = None

    for conn in connections:
        if conn["token_expiry"]:
            if conn["token_expiry"] < now:
                expired_count += 1
            if latest_expiry is None or conn["token_expiry"] > latest_expiry:
                latest_expiry = conn["token_expiry"]

        if latest_updated is None or (conn["updated_at"] and conn["updated_at"] > latest_updated):
            latest_updated = conn["updated_at"]

    return expired_count, latest_expiry, latest_updated


def build_connector_status(
    service: str, requires_oauth: bool, connections: list[dict[str, Any]], now: datetime
) -> ConnectorStatus:
    """Build ConnectorStatus for a single service."""
    connection_count = len(connections)

    if connection_count == 0:
        return ConnectorStatus(
            service=service,
            credential_status="missing",
            requires_oauth=requires_oauth,
            connection_count=0,
        )

    expired_count, latest_expiry, latest_updated = analyze_connections(connections, now)

    if expired_count == connection_count and requires_oauth:
        status = "expired"
    elif expired_count > 0:
        status = "partially_expired"
    else:
        status = "connected"

    return ConnectorStatus(
        service=service,
        credential_status=status,
        token_expiry=latest_expiry,
        last_updated=latest_updated,
        requires_oauth=requires_oauth,
        connection_count=connection_count,
    )


def get_credential_with_fallback(
    org_id: str, user_id: str, service: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Try to get credential, first as customer then as agent. Returns (cred, type)."""
    cred = CredentialManager.get_credential(
        org_id=org_id, user_id=user_id, service=service, credential_type="customer"
    )
    if cred:
        return cred, "customer"

    cred = CredentialManager.get_credential(
        org_id=org_id, user_id=user_id, service=service, credential_type="agent"
    )
    if cred:
        return cred, "agent"

    return None, None


def build_workflow_connector_status(
    service: str, org_id: str, user_id: str, now: datetime
) -> WorkflowConnectorStatus:
    """Build WorkflowConnectorStatus for a single service."""
    requires_oauth = WORKFLOW_OAUTH_REQUIREMENTS.get(service, False)
    display_name = SERVICE_DISPLAY_NAMES.get(service, service.title())

    if not requires_oauth:
        return WorkflowConnectorStatus(
            kind=service,
            display_name=display_name,
            status="connected",
            requires_oauth=False,
            credential_type=None,
            token_expiry=None,
            last_updated=None,
        )

    cred, credential_type = get_credential_with_fallback(org_id, user_id, service)

    if not cred:
        return WorkflowConnectorStatus(
            kind=service,
            display_name=display_name,
            status="missing",
            requires_oauth=True,
            credential_type=None,
            token_expiry=None,
            last_updated=None,
        )

    token_expiry = cred.get("token_expiry")
    is_expired = token_expiry and token_expiry < now

    return WorkflowConnectorStatus(
        kind=service,
        display_name=display_name,
        status="expired" if is_expired else "connected",
        requires_oauth=True,
        credential_type=credential_type,
        token_expiry=token_expiry,
        last_updated=cred.get("updated_at"),
    )


def aggregate_connector_status(connectors: list[WorkflowConnectorStatus]) -> tuple[bool, int]:
    """Calculate all_connected and missing_count from connector list."""
    oauth_connectors = [c for c in connectors if c.requires_oauth]
    all_connected = all(c.status == "connected" for c in oauth_connectors)
    missing_count = sum(1 for c in oauth_connectors if c.status in ["missing", "expired"])
    return all_connected, missing_count
