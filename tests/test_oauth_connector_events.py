"""OAuth success redirect should emit connector lifecycle events."""

from unittest.mock import Mock

from app.routers.oauth.base import build_oauth_success_redirect


def test_oauth_success_redirect_emits_connector_event(monkeypatch) -> None:
    """OAuth success should emit connector.connected to Baby MARS."""
    post_mock = Mock()
    post_mock.return_value.status_code = 202

    monkeypatch.setenv("BABY_MARS_WEBHOOK_URL", "http://mars.test/webhooks/stargate")
    monkeypatch.setenv("API_SECRET_KEY", "test-api-key")
    monkeypatch.setenv("N3_FRONTEND_URL", "http://n3.test")
    monkeypatch.setattr("app.routers.oauth.base.requests.post", post_mock)

    response = build_oauth_success_redirect(
        service="quickbooks",
        org_id="org_test",
        user_id="user_test",
        extra_params={"source": "chat"},
    )

    assert response.status_code == 302
    assert response.headers["location"].startswith("http://n3.test/settings/integrations")
    post_mock.assert_called_once()

    _, kwargs = post_mock.call_args
    assert kwargs["headers"]["X-API-Key"] == "test-api-key"
    assert kwargs["timeout"] == 2

    event = kwargs["json"]
    assert event["event_type"] == "connector.connected"
    assert event["source_service"] == "stargate"
    assert event["org_id"] == "org_test"
    assert event["user_id"] == "user_test"
    assert event["payload"]["platform"] == "quickbooks"
    assert event["payload"]["origin"] == "oauth_callback"


def test_oauth_success_redirect_skips_emit_when_not_configured(monkeypatch) -> None:
    """No webhook config should keep redirect behavior without posting."""
    post_mock = Mock()
    monkeypatch.delenv("BABY_MARS_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("API_SECRET_KEY", raising=False)
    monkeypatch.setattr("app.routers.oauth.base.requests.post", post_mock)

    response = build_oauth_success_redirect(
        service="xero",
        org_id="org_test",
        user_id="user_test",
    )

    assert response.status_code == 302
    post_mock.assert_not_called()
