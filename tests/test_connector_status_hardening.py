from datetime import UTC, datetime

import pytest

from app.constants.services import WORKFLOW_OAUTH_REQUIREMENTS
from app.models import ConnectorStatusRequest, WorkflowConnectorStatus
from app.routers import connectors as connectors_router
from app.services import connector_health


def test_workflow_oauth_requirements_include_n3_services() -> None:
    required = {
        "quickbooks",
        "xero",
        "netsuite",
        "slack",
        "gmail",
        "google",
        "hubspot",
        "chase",
        "brex",
        "billcom",
        "linear",
        "asana",
        "clickup",
        "notion",
        "ramp",
        "docusign",
        "gusto",
        "shopify",
        "square",
        "sage_intacct",
        "airtable",
        "monday",
        "dropbox",
        "powerbi",
    }
    missing = sorted(svc for svc in required if svc not in WORKFLOW_OAUTH_REQUIREMENTS)
    assert not missing, f"Missing OAuth requirement entries: {missing}"
    assert WORKFLOW_OAUTH_REQUIREMENTS["dropbox"] is True


def test_dropbox_status_requires_auth_and_missing_when_no_credential(monkeypatch) -> None:
    monkeypatch.setattr(
        connector_health,
        "get_credential_with_fallback",
        lambda org_id, user_id, service: (None, None),
    )
    status = connector_health.build_workflow_connector_status(
        "dropbox",
        "org_1",
        "user_1",
        datetime.now(UTC),
    )
    assert status.kind == "dropbox"
    assert status.requires_oauth is True
    assert status.status == "missing"


def test_unknown_service_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        connector_health,
        "get_credential_with_fallback",
        lambda org_id, user_id, service: (None, None),
    )
    status = connector_health.build_workflow_connector_status(
        "unknown_service",
        "org_1",
        "user_1",
        datetime.now(UTC),
    )
    assert status.requires_oauth is True
    assert status.status == "missing"


def test_normalize_services_dedupes_and_lowers() -> None:
    assert connectors_router._normalize_services(
        [" QuickBooks ", "quickbooks", "PLAID", "plaid", "", "   "]
    ) == ["quickbooks", "plaid"]


@pytest.mark.asyncio
async def test_connectors_status_route_uses_normalized_services(monkeypatch) -> None:
    calls: list[str] = []

    def _fake_build(service: str, org_id: str, user_id: str, now: datetime) -> WorkflowConnectorStatus:
        calls.append(service)
        return WorkflowConnectorStatus(
            kind=service,
            display_name=service.title(),
            status="connected",
            requires_oauth=True,
            credential_type="customer",
            token_expiry=None,
            last_updated=None,
        )

    monkeypatch.setattr(connectors_router, "build_workflow_connector_status", _fake_build)
    monkeypatch.setattr(
        connectors_router,
        "aggregate_connector_status",
        lambda statuses: (True, 0),
    )

    request = ConnectorStatusRequest(
        org_id="org_123",
        user_id="user_456",
        services=[" QuickBooks ", "quickbooks", "PLAID", "", "plaid "],
    )

    result = await connectors_router.check_workflow_connector_status(request, True)
    assert calls == ["quickbooks", "plaid"]
    assert [c.kind for c in result.connectors] == ["quickbooks", "plaid"]


@pytest.mark.asyncio
async def test_connectors_status_route_fails_closed_after_normalization() -> None:
    request = ConnectorStatusRequest(
        org_id="org_123",
        user_id="user_456",
        services=[" ", "   "],
    )
    result = await connectors_router.check_workflow_connector_status(request, True)
    assert result.connectors == []
    assert result.all_connected is False
    assert result.missing_count == 1
