from unittest.mock import AsyncMock

import pytest

from app.errors import CredentialInvalidError, ErrorCode
from app.models import ToolExecutionRequest
from app.services import execution


@pytest.mark.asyncio
async def test_handle_stargate_error_marks_customer_credential_invalid(monkeypatch) -> None:
    request = ToolExecutionRequest(
        capability_key="vendor.list",
        org_id="org_123",
        user_id="user_456",
        turn_id="turn_789",
        args={},
        session_id="session_abc123",
    )
    capability = {
        "tool_name": "quickbooks.list_vendors",
        "service": "quickbooks",
        "credential_type": "customer",
    }
    error = CredentialInvalidError("quickbooks", "Authentication failed")

    monkeypatch.setattr(execution, "sentry_capture_connector_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "track_connector_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "increment_metric", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "maybe_emit_delivery_event", AsyncMock())
    monkeypatch.setattr(execution.redis_client, "cache_response", lambda *args, **kwargs: None)

    updated: dict[str, object] = {}

    def _fake_update_auth_state(
        org_id: str,
        user_id: str,
        service: str,
        credential_type: str,
        *,
        auth_status: str,
        error_code: str | None = None,
        failure_reason: str | None = None,
    ) -> bool:
        updated.update(
            {
                "org_id": org_id,
                "user_id": user_id,
                "service": service,
                "credential_type": credential_type,
                "auth_status": auth_status,
                "error_code": error_code,
                "failure_reason": failure_reason,
            }
        )
        return True

    emitted: dict[str, object] = {}

    async def _fake_emit_connector_lifecycle_event(**kwargs):
        emitted.update(kwargs)
        return True

    monkeypatch.setattr(
        execution.CredentialManager,
        "update_credential_auth_state",
        _fake_update_auth_state,
    )
    monkeypatch.setattr(
        execution,
        "emit_connector_lifecycle_event",
        _fake_emit_connector_lifecycle_event,
    )

    result = await execution.handle_stargate_error(
        error,
        request,
        capability,
        logs=[],
        start_time=0.0,
        session_id="session_abc123",
    )

    assert result["status"] == "error"
    assert result["error_code"] == ErrorCode.CREDENTIALS_INVALID
    assert result["connect_url"]
    assert updated["service"] == "quickbooks"
    assert updated["credential_type"] == "customer"
    assert updated["auth_status"] == "expired"
    assert emitted["status"] == "expired"
    assert emitted["source"] == "chat__session_abc123"


@pytest.mark.asyncio
async def test_execute_handler_retries_once_after_quickbooks_refresh(monkeypatch) -> None:
    request = ToolExecutionRequest(
        capability_key="vendor.list",
        org_id="org_123",
        user_id="user_456",
        turn_id="turn_789",
        args={},
    )
    capability = {
        "tool_name": "quickbooks.list_vendors",
        "service": "quickbooks",
        "credential_type": "customer",
        "handler": None,
    }
    calls = {"count": 0}

    def _handler(*, org_id: str, user_id: str, args: dict[str, object]):
        calls["count"] += 1
        if calls["count"] == 1:
            raise CredentialInvalidError("quickbooks", "Authentication failed")
        return {"vendors": []}

    capability["handler"] = _handler

    monkeypatch.setattr(execution, "record_success", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "record_failure", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "increment_metric", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "track_capability_called", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "set_user_context", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "set_capability_context", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "add_breadcrumb", lambda *args, **kwargs: None)
    monkeypatch.setattr(execution, "is_open", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        execution,
        "_refresh_quickbooks_credentials",
        lambda org_id, user_id, credential_type: True,
    )

    outputs, _duration = await execution.execute_handler(capability, request, logs=[])

    assert outputs == {"vendors": []}
    assert calls["count"] == 2


def test_connected_merge_clears_auth_invalid_metadata() -> None:
    from app.database import _merge_credential_extra_data, credential_auth_status_is_invalid

    expired = _merge_credential_extra_data(
        {"team_id": "team_123"},
        None,
        auth_status="expired",
        error_code="CREDENTIALS_INVALID",
        failure_reason="Authentication failed",
    )
    assert credential_auth_status_is_invalid(expired) is True

    connected = _merge_credential_extra_data(
        expired,
        None,
        auth_status="connected",
    )
    assert connected["team_id"] == "team_123"
    assert credential_auth_status_is_invalid(connected) is False
