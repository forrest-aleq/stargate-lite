from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.constants import services as service_constants
from app.constants.services import WORKFLOW_OAUTH_REQUIREMENTS
from app.models import (
    ConnectedServicesRequest,
    ConnectorStatusRequest,
    WorkflowConnectorStatus,
)
from app.routers import connectors as connectors_router, health as health_router
from app.routers.oauth.base import build_oauth_success_redirect
from app.services import connector_health


def test_workflow_oauth_requirements_include_n3_services() -> None:
    required = {
        "quickbooks",
        "zoho_books",
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


def test_non_oauth_service_is_missing_without_credential(monkeypatch) -> None:
    monkeypatch.setattr(
        connector_health,
        "get_credential_with_fallback",
        lambda org_id, user_id, service: (None, None),
    )
    status = connector_health.build_workflow_connector_status(
        "stripe",
        "org_1",
        "user_1",
        datetime.now(UTC),
    )
    assert status.kind == "stripe"
    assert status.requires_oauth is False
    assert status.status == "missing"


def test_non_oauth_service_connected_with_credential(monkeypatch) -> None:
    now = datetime.now(UTC)
    mock_cred = {"token_expiry": None, "updated_at": now}
    monkeypatch.setattr(
        connector_health,
        "get_credential_with_fallback",
        lambda org_id, user_id, service: (mock_cred, "customer"),
    )
    status = connector_health.build_workflow_connector_status(
        "plaid",
        "org_1",
        "user_1",
        now,
    )
    assert status.kind == "plaid"
    assert status.requires_oauth is False
    assert status.status == "connected"
    assert status.credential_type == "customer"


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


def test_aggregate_counts_missing_for_non_oauth_services() -> None:
    connectors = [
        WorkflowConnectorStatus(
            kind="quickbooks",
            display_name="QuickBooks",
            status="connected",
            requires_oauth=True,
            credential_type="customer",
            token_expiry=None,
            last_updated=None,
        ),
        WorkflowConnectorStatus(
            kind="stripe",
            display_name="Stripe",
            status="missing",
            requires_oauth=False,
            credential_type=None,
            token_expiry=None,
            last_updated=None,
        ),
    ]
    all_connected, missing_count = connector_health.aggregate_connector_status(connectors)
    assert all_connected is False
    assert missing_count == 1


def test_normalize_services_dedupes_and_lowers() -> None:
    assert connectors_router._normalize_services(
        [" QuickBooks ", "quickbooks", "PLAID", "plaid", "", "   "]
    ) == ["quickbooks", "plaid"]


def test_customer_connectable_services_require_complete_env(monkeypatch) -> None:
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_CLIENT_ID", raising=False)
    monkeypatch.delenv("STRIPE_REDIRECT_URI", raising=False)

    assert service_constants.service_is_customer_connectable("stripe") is False

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    monkeypatch.setenv("STRIPE_CLIENT_ID", "ca_123")
    monkeypatch.setenv("STRIPE_REDIRECT_URI", "https://example.com/oauth/stripe/callback")

    assert service_constants.service_is_customer_connectable("stripe") is True


def test_customer_connectable_services_fail_closed_for_unknown_service() -> None:
    assert service_constants.service_is_customer_connectable("unknown_service") is False


@pytest.mark.asyncio
async def test_connector_health_route_surfaces_all_enabled_services(monkeypatch) -> None:
    monkeypatch.setattr(health_router.CredentialManager, "get_all_credentials", lambda: [])
    monkeypatch.setattr(
        health_router,
        "get_customer_facing_enabled_services",
        lambda: {"quickbooks": True, "plaid": False},
    )

    result = await health_router.connector_health_check()

    assert [connector.service for connector in result.connectors] == ["plaid", "quickbooks"]
    assert [connector.configured for connector in result.connectors] == [False, False]


@pytest.mark.asyncio
async def test_connectors_status_route_uses_normalized_services(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_build_many(
        services: list[str], credentials: list[dict[str, object]], now: datetime
    ) -> list[WorkflowConnectorStatus]:
        calls.append(services)
        return [
            WorkflowConnectorStatus(
                kind=service,
                display_name=service.title(),
                status="connected",
                requires_oauth=True,
                credential_type="customer",
                token_expiry=None,
                last_updated=None,
            )
            for service in services
        ]

    monkeypatch.setattr(
        connectors_router.CredentialManager,
        "get_credentials_for_org_user",
        lambda org_id, user_id: [],
    )
    monkeypatch.setattr(connectors_router, "build_workflow_connector_statuses", _fake_build_many)
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
    assert calls == [["quickbooks", "plaid"]]
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


def test_build_workflow_connector_statuses_prefers_customer_and_latest_record() -> None:
    now = datetime.now(UTC)
    statuses = connector_health.build_workflow_connector_statuses(
        ["quickbooks"],
        [
            {
                "service": "quickbooks",
                "credential_type": "agent",
                "token_expiry": None,
                "updated_at": now.replace(hour=1),
            },
            {
                "service": "quickbooks",
                "credential_type": "customer",
                "token_expiry": None,
                "updated_at": now.replace(hour=2),
            },
        ],
        now,
    )

    assert len(statuses) == 1
    assert statuses[0].status == "connected"
    assert statuses[0].credential_type == "customer"


def test_build_workflow_connector_status_marks_auth_invalid_even_before_token_expiry() -> None:
    now = datetime.now(UTC)
    statuses = connector_health.build_workflow_connector_statuses(
        ["quickbooks"],
        [
            {
                "service": "quickbooks",
                "credential_type": "customer",
                "token_expiry": now.replace(year=now.year + 1),
                "updated_at": now,
                "extra_data": {
                    "_aleq_credential_health": {
                        "auth_status": "expired",
                    }
                },
            }
        ],
        now,
    )

    assert len(statuses) == 1
    assert statuses[0].status == "expired"
    assert statuses[0].credential_type == "customer"


@pytest.mark.asyncio
async def test_connected_services_route_returns_connected_and_expired(monkeypatch) -> None:
    now = datetime.now(UTC)
    monkeypatch.setattr(
        connectors_router.CredentialManager,
        "get_credentials_for_org_user",
        lambda org_id, user_id: [
            {
                "service": "quickbooks",
                "credential_type": "customer",
                "token_expiry": None,
                "updated_at": now,
                "extra_data": {},
            },
            {
                "service": "xero",
                "credential_type": "customer",
                "token_expiry": now.replace(year=now.year + 1),
                "updated_at": now,
                "extra_data": {
                    "_aleq_credential_health": {
                        "auth_status": "expired",
                    }
                },
            },
        ],
    )

    result = await connectors_router.get_connected_services(
        ConnectedServicesRequest(org_id="org_123", user_id="user_456"),
        True,
    )

    assert result.connected_services == ["quickbooks"]
    assert result.expired_services == ["xero"]


def test_oauth_success_redirect_emits_source_in_connector_event(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_post(url: str, json: dict[str, object], headers: dict[str, str], timeout: int):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return SimpleNamespace(status_code=200)

    monkeypatch.setenv("BABY_MARS_WEBHOOK_URL", "https://baby-mars.example/webhooks/stargate")
    monkeypatch.setenv("API_SECRET_KEY", "test-secret")
    monkeypatch.setenv("N3_FRONTEND_URL", "https://aleq.example")
    monkeypatch.setattr("app.routers.oauth.base.requests.post", _fake_post)

    response = build_oauth_success_redirect(
        "quickbooks",
        org_id="org_1",
        user_id="user_1",
        extra_params={"source": "chat__session_abc123def456"},
    )

    assert response.headers["location"].startswith(
        "https://aleq.example/auth/integrations/callback?connected=quickbooks"
    )
    payload = captured["json"]
    assert isinstance(payload, dict)
    event_payload = payload["payload"]
    assert isinstance(event_payload, dict)
    assert event_payload["source"] == "chat__session_abc123def456"
