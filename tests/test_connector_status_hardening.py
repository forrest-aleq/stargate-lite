from datetime import UTC, datetime

from app.constants.services import WORKFLOW_OAUTH_REQUIREMENTS
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
