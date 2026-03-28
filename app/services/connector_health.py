"""
Connector health service - Helper functions for analyzing connector/credential status.
"""

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from app.constants.services import (
    ALL_SERVICES_OAUTH,
    SERVICE_DISPLAY_NAMES,
    WORKFLOW_OAUTH_REQUIREMENTS,
)
from app.database import CredentialManager, credential_auth_status_is_invalid
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
        token_expiry = conn["token_expiry"]
        if token_expiry:
            # Normalize to UTC-aware for comparison (Supabase returns tz-aware)
            if token_expiry.tzinfo is None:
                token_expiry = token_expiry.replace(tzinfo=UTC)
            if token_expiry < now:
                expired_count += 1
            if latest_expiry is None or token_expiry > latest_expiry:
                latest_expiry = token_expiry

        updated_at = conn["updated_at"]
        if updated_at:
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=UTC)
            if latest_updated is None or updated_at > latest_updated:
                latest_updated = updated_at

    return expired_count, latest_expiry, latest_updated


def build_connector_status(
    service: str,
    requires_oauth: bool,
    configured: bool,
    connections: list[dict[str, Any]],
    now: datetime,
) -> ConnectorStatus:
    """Build ConnectorStatus for a single service."""
    connection_count = len(connections)

    if connection_count == 0:
        return ConnectorStatus(
            service=service,
            credential_status="missing",
            configured=configured,
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
        configured=configured,
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


def _select_preferred_workflow_credential(
    credentials: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    """Pick the credential record that workflow status should reflect.

    Preserve existing behavior: prefer customer credentials over agent credentials,
    then prefer the freshest record within that type.
    """
    if not credentials:
        return None, None

    def _sort_key(item: dict[str, Any]) -> tuple[int, float]:
        cred_type = str(item.get("credential_type") or "")
        updated_at = item.get("updated_at")
        if not isinstance(updated_at, datetime):
            updated_at = datetime.min.replace(tzinfo=UTC)
        elif updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        type_rank = 0 if cred_type == "customer" else 1
        return (-type_rank, updated_at.timestamp())

    preferred = max(credentials, key=_sort_key)
    cred_type = str(preferred.get("credential_type") or "") or None
    return preferred, cred_type


def build_workflow_connector_status_from_credential(
    service: str,
    credential: dict[str, Any] | None,
    credential_type: str | None,
    now: datetime,
) -> WorkflowConnectorStatus:
    """Build workflow connector status from a pre-fetched credential record."""
    requires_oauth = WORKFLOW_OAUTH_REQUIREMENTS.get(service, True)
    display_name = SERVICE_DISPLAY_NAMES.get(service, service.title())

    if not credential:
        return WorkflowConnectorStatus(
            kind=service,
            display_name=display_name,
            status="missing",
            requires_oauth=requires_oauth,
            credential_type=None,
            token_expiry=None,
            last_updated=None,
        )

    token_expiry = credential.get("token_expiry")
    if token_expiry and token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=UTC)
    is_expired = token_expiry and token_expiry < now
    auth_invalid = credential_auth_status_is_invalid(credential.get("extra_data"))

    return WorkflowConnectorStatus(
        kind=service,
        display_name=display_name,
        status="expired" if is_expired or auth_invalid else "connected",
        requires_oauth=requires_oauth,
        credential_type=credential_type,
        token_expiry=token_expiry,
        last_updated=credential.get("updated_at"),
    )


def build_workflow_connector_statuses(
    services: list[str],
    credentials: list[dict[str, Any]],
    now: datetime,
) -> list[WorkflowConnectorStatus]:
    """Build workflow connector statuses from one bulk credential query."""
    credentials_by_service: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for credential in credentials:
        service = str(credential.get("service") or "").strip().lower()
        if not service:
            continue
        credentials_by_service[service].append(credential)

    statuses: list[WorkflowConnectorStatus] = []
    for service in services:
        selected_credential, credential_type = _select_preferred_workflow_credential(
            credentials_by_service.get(service, [])
        )
        statuses.append(
            build_workflow_connector_status_from_credential(
                service,
                selected_credential,
                credential_type,
                now,
            )
        )
    return statuses


def build_workflow_connector_status(
    service: str, org_id: str, user_id: str, now: datetime
) -> WorkflowConnectorStatus:
    """Build WorkflowConnectorStatus for a single service."""
    cred, credential_type = get_credential_with_fallback(org_id, user_id, service)
    return build_workflow_connector_status_from_credential(
        service,
        cred,
        credential_type,
        now,
    )


def aggregate_connector_status(connectors: list[WorkflowConnectorStatus]) -> tuple[bool, int]:
    """Calculate all_connected and missing_count from connector list."""
    all_connected = all(c.status == "connected" for c in connectors)
    missing_count = sum(1 for c in connectors if c.status in ["missing", "expired"])
    return all_connected, missing_count
