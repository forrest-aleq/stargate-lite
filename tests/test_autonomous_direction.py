"""
Tests for Autonomous Direction features (metadata passthrough, webhook forwarding,
delivery events).

Validates:
- metadata field on ToolExecutionRequest
- verb_tier logging and metric tagging
- Webhook forwarding infrastructure
- Delivery events for Tier 3 actions
"""

import asyncio
import contextlib
import os
import time
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app, verify_api_key


# Override API key dependency for all tests
def mock_verify_api_key() -> bool:
    """Mock API key verification - always pass."""
    return True


app.dependency_overrides[verify_api_key] = mock_verify_api_key


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client with API key check disabled."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_redis(client: TestClient) -> Generator[None, None, None]:
    """Clear Redis cache before each test."""
    from app.redis_client import redis_client

    if redis_client._redis_client:
        with contextlib.suppress(Exception):
            redis_client._redis_client.flushdb()
    yield
    if redis_client._redis_client:
        with contextlib.suppress(Exception):
            redis_client._redis_client.flushdb()


# ============================================================================
# Commit 1: metadata field on ToolExecutionRequest
# ============================================================================


class TestMetadataField:
    """Test that ToolExecutionRequest accepts optional metadata."""

    def test_request_accepts_metadata_field(self, client: TestClient) -> None:
        """POST to /api/v1/execute with metadata dict is accepted (not a 422)."""
        with patch("app.routers.execute.get_capability") as mock_cap:
            mock_cap.return_value = {
                "handler": lambda org_id, user_id, args: {"result": "ok"},
                "tool_name": "test.tool",
                "service": "test",
                "credential_type": "agent",
            }

            response = client.post(
                "/api/v1/execute",
                json={
                    "capability_key": "test.action",
                    "org_id": "org_test",
                    "user_id": "user_test",
                    "turn_id": "turn_metadata_test_001",
                    "args": {},
                    "metadata": {
                        "verb_tier": 0,
                        "proactive": False,
                        "trigger_id": None,
                        "belief_context": {},
                    },
                },
            )

            # Should not be a validation error
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_request_works_without_metadata(self, client: TestClient) -> None:
        """Backward-compatible: requests without metadata still work."""
        with patch("app.routers.execute.get_capability") as mock_cap:
            mock_cap.return_value = {
                "handler": lambda org_id, user_id, args: {"result": "ok"},
                "tool_name": "test.tool",
                "service": "test",
                "credential_type": "agent",
            }

            response = client.post(
                "/api/v1/execute",
                json={
                    "capability_key": "test.action",
                    "org_id": "org_test",
                    "user_id": "user_test",
                    "turn_id": "turn_no_metadata_test_001",
                    "args": {},
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


# ============================================================================
# Commit 2: verb_tier logging and metric tagging
# ============================================================================


class TestVerbTierMetrics:
    """Test that verb_tier from metadata is tagged in metrics."""

    def test_verb_tier_from_metadata_tagged_in_metrics(self, client: TestClient) -> None:
        """Send request with metadata.verb_tier=0, verify metric tagged."""
        with (
            patch("app.routers.execute.get_capability") as mock_cap,
            patch("app.services.execution.increment_metric") as mock_metric,
        ):
            mock_cap.return_value = {
                "handler": lambda org_id, user_id, args: {"result": "ok"},
                "tool_name": "test.tool",
                "service": "test",
                "credential_type": "agent",
            }

            client.post(
                "/api/v1/execute",
                json={
                    "capability_key": "test.action",
                    "org_id": "org_test",
                    "user_id": "user_test",
                    "turn_id": "turn_metric_test_001",
                    "args": {},
                    "metadata": {"verb_tier": 0},
                },
            )

            # Check that increment_metric was called with verb_tier tag
            calls = mock_metric.call_args_list
            success_calls = [c for c in calls if "execution.success" in str(c)]
            assert len(success_calls) >= 1
            # Extract tags from the call (keyword arg)
            tag_list: list[str] = success_calls[0].kwargs.get("tags", [])
            assert any("verb_tier:0" in t for t in tag_list)

    def test_verb_tier_unknown_when_no_metadata(self, client: TestClient) -> None:
        """Without metadata, verb_tier defaults to 'unknown' in metrics."""
        with (
            patch("app.routers.execute.get_capability") as mock_cap,
            patch("app.services.execution.increment_metric") as mock_metric,
        ):
            mock_cap.return_value = {
                "handler": lambda org_id, user_id, args: {"result": "ok"},
                "tool_name": "test.tool",
                "service": "test",
                "credential_type": "agent",
            }

            client.post(
                "/api/v1/execute",
                json={
                    "capability_key": "test.action",
                    "org_id": "org_test",
                    "user_id": "user_test",
                    "turn_id": "turn_no_tier_test_001",
                    "args": {},
                },
            )

            calls = mock_metric.call_args_list
            success_calls = [c for c in calls if "execution.success" in str(c)]
            assert len(success_calls) >= 1
            tag_list: list[str] = success_calls[0].kwargs.get("tags", [])
            assert any("verb_tier:unknown" in t for t in tag_list)


# ============================================================================
# Commit 4: Webhook event model + forwarding infrastructure
# ============================================================================


class TestWebhookEventModel:
    """Test WebhookEvent model validation."""

    def test_webhook_event_requires_raw_event_id(self) -> None:
        """raw_event_id is required — ValidationError without it."""
        from pydantic import ValidationError

        from app.models_webhook import WebhookEvent

        with pytest.raises(ValidationError, match="raw_event_id"):
            WebhookEvent(
                event_type="test.event",
                source_service="test",
                org_id="org_test",
                timestamp=datetime.now(UTC),
                payload={"key": "value"},
                # raw_event_id intentionally missing
            )

    def test_webhook_event_accepts_all_fields(self) -> None:
        """Full WebhookEvent creation succeeds."""
        from app.models_webhook import WebhookEvent

        event = WebhookEvent(
            event_type="stripe.payment.succeeded",
            source_service="stripe",
            org_id="org_123",
            timestamp=datetime.now(UTC),
            payload={"amount": 1000},
            raw_event_id="evt_abc123",
            user_id="user_456",
        )
        assert event.event_type == "stripe.payment.succeeded"
        assert event.raw_event_id == "evt_abc123"


class TestWebhookForwarding:
    """Test forwarding infrastructure."""

    def test_forward_skips_when_no_url(self) -> None:
        """No crash when BABY_MARS_WEBHOOK_URL is unset."""
        from app.models_webhook import WebhookEvent

        event = WebhookEvent(
            event_type="test.event",
            source_service="test",
            org_id="org_test",
            timestamp=datetime.now(UTC),
            payload={},
            raw_event_id="evt_test_001",
        )

        with patch("app.routers.webhooks.base.BABY_MARS_WEBHOOK_URL", ""):
            from app.routers.webhooks.base import forward_to_baby_mars

            result = asyncio.get_event_loop().run_until_complete(forward_to_baby_mars(event))
            assert result is False

    def test_forward_deduplicates_by_raw_event_id(self) -> None:
        """Send same event twice, second call is deduped."""
        from app.models_webhook import WebhookEvent

        event = WebhookEvent(
            event_type="test.event",
            source_service="test",
            org_id="org_test",
            timestamp=datetime.now(UTC),
            payload={},
            raw_event_id="evt_dedup_001",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch(
                "app.routers.webhooks.base.BABY_MARS_WEBHOOK_URL",
                "http://mars.test/webhooks/stargate",
            ),
            patch("app.routers.webhooks.base._get_forward_session") as mock_session_fn,
        ):
            mock_session = MagicMock()
            mock_session.post.return_value = mock_response
            mock_session_fn.return_value = mock_session

            from app.routers.webhooks.base import forward_to_baby_mars

            loop = asyncio.get_event_loop()

            # First call — should forward
            result1 = loop.run_until_complete(forward_to_baby_mars(event))
            assert result1 is True

            # Second call — should be deduped (no second HTTP call)
            result2 = loop.run_until_complete(forward_to_baby_mars(event))
            assert result2 is True

            # HTTP POST should only have been called once
            assert mock_session.post.call_count == 1

    def test_forward_retries_on_failure(self) -> None:
        """Mock HTTP failure, verify 4 attempts (1 initial + 3 retries)."""
        from app.models_webhook import WebhookEvent

        event = WebhookEvent(
            event_type="test.event",
            source_service="test",
            org_id="org_test",
            timestamp=datetime.now(UTC),
            payload={},
            raw_event_id="evt_retry_001",
        )

        mock_response = MagicMock()
        mock_response.status_code = 500  # Server error — triggers retry

        with (
            patch(
                "app.routers.webhooks.base.BABY_MARS_WEBHOOK_URL",
                "http://mars.test/webhooks/stargate",
            ),
            patch("app.routers.webhooks.base._get_forward_session") as mock_session_fn,
            patch("app.routers.webhooks.base.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_session = MagicMock()
            mock_session.post.return_value = mock_response
            mock_session_fn.return_value = mock_session

            from app.routers.webhooks.base import forward_to_baby_mars

            result = asyncio.get_event_loop().run_until_complete(forward_to_baby_mars(event))
            assert result is False
            assert mock_session.post.call_count == 4  # 1 initial + 3 retries


# ============================================================================
# Commit 5: Stripe + QBO + Xero webhook receivers
# ============================================================================


class TestStripeWebhook:
    """Test Stripe webhook receiver."""

    def _make_stripe_signature(
        self, payload: bytes, secret: str, timestamp: str | None = None
    ) -> str:
        """Build a valid Stripe-Signature header."""
        import hashlib
        import hmac as _hmac

        ts = timestamp or str(int(time.time()))
        signed_payload = f"{ts}.".encode() + payload
        sig = _hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        return f"t={ts},v1={sig}"

    def test_stripe_rejects_invalid_signature(self, client: TestClient) -> None:
        """Invalid Stripe signature returns 401."""
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test123"}):
            response = client.post(
                "/webhooks/stripe",
                content=b'{"type": "payment_intent.succeeded", "id": "evt_001"}',
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "t=1234567890,v1=invalidsignature",
                },
            )
            assert response.status_code == 401

    def test_stripe_normalizes_payment_event(self, client: TestClient) -> None:
        """Valid Stripe event is accepted and forwarded."""
        secret = "whsec_test_secret"
        payload = b'{"type": "payment_intent.succeeded", "id": "evt_pi_001", "account": "acct_123"}'

        sig = self._make_stripe_signature(payload, secret)

        with (
            patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": secret}),
            patch(
                "app.routers.webhooks.stripe.forward_to_baby_mars", new_callable=AsyncMock
            ) as mock_fwd,
        ):
            mock_fwd.return_value = True
            response = client.post(
                "/webhooks/stripe",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": sig,
                },
            )
            assert response.status_code == 200
            assert mock_fwd.called
            forwarded_event = mock_fwd.call_args[0][0]
            assert forwarded_event.event_type == "stripe.payment_intent.succeeded"
            assert forwarded_event.org_id == "acct_123"

    def test_stripe_resolves_internal_tenant_identity(self, client: TestClient) -> None:
        """Stripe webhook uses credential-backed identity when available."""
        secret = "whsec_test_secret"
        payload = b'{"type": "payment_intent.succeeded", "id": "evt_pi_002", "account": "acct_456"}'
        sig = self._make_stripe_signature(payload, secret)

        with (
            patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": secret}),
            patch(
                "app.routers.webhooks.stripe.resolve_webhook_identity",
                new_callable=AsyncMock,
            ) as mock_resolve,
            patch(
                "app.routers.webhooks.stripe.forward_to_baby_mars", new_callable=AsyncMock
            ) as mock_fwd,
        ):
            mock_resolve.return_value = ("org_internal", "user_internal")
            mock_fwd.return_value = True

            response = client.post(
                "/webhooks/stripe",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": sig,
                },
            )

            assert response.status_code == 200
            forwarded_event = mock_fwd.call_args[0][0]
            assert forwarded_event.org_id == "org_internal"
            assert forwarded_event.user_id == "user_internal"


class TestQBOWebhook:
    """Test QuickBooks Online webhook receiver."""

    def test_qbo_challenge_response(self, client: TestClient) -> None:
        """QBO verification challenge returns correct HMAC."""
        import hashlib
        import hmac as _hmac

        verifier = "test_verifier_token"
        challenge = "challenge_abc"

        expected_hash = _hmac.new(verifier.encode(), challenge.encode(), hashlib.sha256).hexdigest()

        with patch.dict(os.environ, {"QBO_WEBHOOK_VERIFIER_TOKEN": verifier}):
            response = client.post(
                "/webhooks/quickbooks",
                json={"verifier_token": challenge},
            )
            assert response.status_code == 200
            assert response.text == expected_hash

    def test_qbo_normalizes_transaction_event(self, client: TestClient) -> None:
        """QBO entity change notification is normalized and forwarded."""
        import hashlib
        import hmac as _hmac

        verifier = "test_verifier_token"
        payload_dict: dict[str, Any] = {
            "eventNotifications": [
                {
                    "realmId": "realm_123",
                    "dataChangeEvent": {
                        "entities": [{"name": "Invoice", "id": "inv_001", "operation": "Create"}]
                    },
                }
            ]
        }
        import json

        payload_bytes = json.dumps(payload_dict).encode()
        sig = _hmac.new(verifier.encode(), payload_bytes, hashlib.sha256).hexdigest()

        with (
            patch.dict(os.environ, {"QBO_WEBHOOK_VERIFIER_TOKEN": verifier}),
            patch(
                "app.routers.webhooks.quickbooks.forward_to_baby_mars", new_callable=AsyncMock
            ) as mock_fwd,
        ):
            mock_fwd.return_value = True
            response = client.post(
                "/webhooks/quickbooks",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "intuit-signature": sig,
                },
            )
            assert response.status_code == 200
            assert mock_fwd.called
            forwarded_event = mock_fwd.call_args[0][0]
            assert forwarded_event.event_type == "qbo.invoice.create"
            assert forwarded_event.org_id == "realm_123"

    def test_qbo_resolves_internal_tenant_identity(self, client: TestClient) -> None:
        """QBO webhook uses credential-backed identity when available."""
        import hashlib
        import hmac as _hmac
        import json

        verifier = "test_verifier_token"
        payload_dict: dict[str, Any] = {
            "eventNotifications": [
                {
                    "realmId": "realm_456",
                    "dataChangeEvent": {
                        "entities": [{"name": "Invoice", "id": "inv_002", "operation": "Create"}]
                    },
                }
            ]
        }
        payload_bytes = json.dumps(payload_dict).encode()
        sig = _hmac.new(verifier.encode(), payload_bytes, hashlib.sha256).hexdigest()

        with (
            patch.dict(os.environ, {"QBO_WEBHOOK_VERIFIER_TOKEN": verifier}),
            patch(
                "app.routers.webhooks.quickbooks.resolve_webhook_identity",
                new_callable=AsyncMock,
            ) as mock_resolve,
            patch(
                "app.routers.webhooks.quickbooks.forward_to_baby_mars",
                new_callable=AsyncMock,
            ) as mock_fwd,
        ):
            mock_resolve.return_value = ("org_internal_qbo", "user_internal_qbo")
            mock_fwd.return_value = True

            response = client.post(
                "/webhooks/quickbooks",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "intuit-signature": sig,
                },
            )

            assert response.status_code == 200
            forwarded_event = mock_fwd.call_args[0][0]
            assert forwarded_event.org_id == "org_internal_qbo"
            assert forwarded_event.user_id == "user_internal_qbo"


class TestXeroWebhook:
    """Test Xero webhook receiver."""

    def test_xero_intent_to_receive_validation(self, client: TestClient) -> None:
        """Xero intent-to-receive: valid sig + empty events = 200."""
        import hashlib
        import hmac as _hmac

        webhook_key = "xero_test_key"
        payload = b'{"events": []}'
        sig = _hmac.new(webhook_key.encode(), payload, hashlib.sha256).hexdigest()

        with patch.dict(os.environ, {"XERO_WEBHOOK_KEY": webhook_key}):
            response = client.post(
                "/webhooks/xero",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-xero-signature": sig,
                },
            )
            assert response.status_code == 200

    def test_xero_resolves_internal_tenant_identity(self, client: TestClient) -> None:
        """Xero webhook uses credential-backed identity when available."""
        import hashlib
        import hmac as _hmac

        webhook_key = "xero_test_key"
        payload = b'{"events":[{"tenantId":"tenant_123","eventCategory":"INVOICE","eventType":"CREATE","eventId":"evt_xero_001","resourceUrl":"https://api.xero.com/api.xro/2.0/Invoices/1"}]}'
        sig = _hmac.new(webhook_key.encode(), payload, hashlib.sha256).hexdigest()

        with (
            patch.dict(os.environ, {"XERO_WEBHOOK_KEY": webhook_key}),
            patch(
                "app.routers.webhooks.xero.resolve_webhook_identity",
                new_callable=AsyncMock,
            ) as mock_resolve,
            patch(
                "app.routers.webhooks.xero.forward_to_baby_mars", new_callable=AsyncMock
            ) as mock_fwd,
        ):
            mock_resolve.return_value = ("org_internal_xero", "user_internal_xero")
            mock_fwd.return_value = True

            response = client.post(
                "/webhooks/xero",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-xero-signature": sig,
                },
            )

            assert response.status_code == 200
            forwarded_event = mock_fwd.call_args[0][0]
            assert forwarded_event.org_id == "org_internal_xero"
            assert forwarded_event.user_id == "user_internal_xero"


# ============================================================================
# Commit 6: Slack + Twilio webhook receivers
# ============================================================================


class TestSlackWebhook:
    """Test Slack webhook receiver."""

    def test_slack_url_verification_challenge(self, client: TestClient) -> None:
        """Slack URL verification returns the challenge token."""
        with patch.dict(os.environ, {"SLACK_SIGNING_SECRET": "test_secret"}):
            response = client.post(
                "/webhooks/slack",
                json={"type": "url_verification", "challenge": "abc123xyz"},
            )
            assert response.status_code == 200
            assert response.json() == {"challenge": "abc123xyz"}

    def test_slack_dm_normalizes_and_forwards(self, client: TestClient) -> None:
        """Slack DM event is normalized and forwarded."""
        import hashlib
        import hmac as _hmac
        import json

        signing_secret = "slack_test_secret_key"
        payload_dict: dict[str, Any] = {
            "type": "event_callback",
            "team_id": "T_TESTTEAM",
            "event_id": "Ev_TEST001",
            "event": {
                "type": "message",
                "channel_type": "im",
                "user": "U_TESTUSER",
                "text": "hello aleq",
            },
        }
        payload_bytes = json.dumps(payload_dict).encode()
        timestamp = str(int(time.time()))
        base_string = f"v0:{timestamp}:".encode() + payload_bytes
        sig = "v0=" + _hmac.new(signing_secret.encode(), base_string, hashlib.sha256).hexdigest()

        with (
            patch.dict(os.environ, {"SLACK_SIGNING_SECRET": signing_secret}),
            patch(
                "app.routers.webhooks.slack.forward_to_baby_mars",
                new_callable=AsyncMock,
            ) as mock_fwd,
        ):
            mock_fwd.return_value = True
            response = client.post(
                "/webhooks/slack",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Slack-Request-Timestamp": timestamp,
                    "X-Slack-Signature": sig,
                },
            )
            assert response.status_code == 200
            assert mock_fwd.called
            forwarded_event = mock_fwd.call_args[0][0]
            assert forwarded_event.event_type == "slack.message.received"
            assert forwarded_event.org_id == "T_TESTTEAM"
            assert forwarded_event.user_id == "U_TESTUSER"

    def test_slack_resolves_internal_tenant_identity(self, client: TestClient) -> None:
        """Slack webhook uses credential-backed identity when available."""
        import hashlib
        import hmac as _hmac
        import json

        signing_secret = "slack_test_secret_key"
        payload_dict: dict[str, Any] = {
            "type": "event_callback",
            "team_id": "T_RESOLVE",
            "event_id": "Ev_RESOLVE001",
            "event": {
                "type": "message",
                "channel_type": "im",
                "user": "U_EXTERNAL",
                "text": "hello aleq",
            },
        }
        payload_bytes = json.dumps(payload_dict).encode()
        timestamp = str(int(time.time()))
        base_string = f"v0:{timestamp}:".encode() + payload_bytes
        sig = "v0=" + _hmac.new(signing_secret.encode(), base_string, hashlib.sha256).hexdigest()

        with (
            patch.dict(os.environ, {"SLACK_SIGNING_SECRET": signing_secret}),
            patch(
                "app.routers.webhooks.slack.resolve_webhook_identity",
                new_callable=AsyncMock,
            ) as mock_resolve,
            patch(
                "app.routers.webhooks.slack.forward_to_baby_mars",
                new_callable=AsyncMock,
            ) as mock_fwd,
        ):
            mock_resolve.return_value = ("org_internal_slack", "user_internal_slack")
            mock_fwd.return_value = True

            response = client.post(
                "/webhooks/slack",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Slack-Request-Timestamp": timestamp,
                    "X-Slack-Signature": sig,
                },
            )

            assert response.status_code == 200
            forwarded_event = mock_fwd.call_args[0][0]
            assert forwarded_event.org_id == "org_internal_slack"
            assert forwarded_event.user_id == "user_internal_slack"


class TestTwilioWebhook:
    """Test Twilio webhook receiver."""

    def _make_twilio_signature(self, url: str, params: dict[str, str], auth_token: str) -> str:
        """Build a valid X-Twilio-Signature header."""
        import base64
        import hashlib
        import hmac as _hmac

        data = url
        for key in sorted(params.keys()):
            data += key + params[key]

        return base64.b64encode(
            _hmac.new(auth_token.encode(), data.encode(), hashlib.sha1).digest()
        ).decode()

    def test_twilio_rejects_invalid_signature(self, client: TestClient) -> None:
        """Invalid Twilio signature returns 401."""
        with patch.dict(os.environ, {"TWILIO_AUTH_TOKEN": "test_token"}):
            response = client.post(
                "/webhooks/twilio",
                data={
                    "MessageSid": "SM_test001",
                    "From": "+15551234567",
                    "To": "+15559876543",
                    "Body": "hello",
                    "AccountSid": "AC_test",
                },
                headers={"X-Twilio-Signature": "invalidsignature"},
            )
            assert response.status_code == 401

    def test_twilio_normalizes_inbound_sms(self, client: TestClient) -> None:
        """Valid Twilio inbound SMS is normalized and forwarded."""
        auth_token = "twilio_test_auth_token"
        params = {
            "MessageSid": "SM_test_msg_001",
            "AccountSid": "AC_test_account",
            "From": "+15551234567",
            "To": "+15559876543",
            "Body": "Hey Aleq, check my invoices",
        }

        # The test client URL — TestClient uses http://testserver by default
        url = "http://testserver/webhooks/twilio"
        sig = self._make_twilio_signature(url, params, auth_token)

        with (
            patch.dict(os.environ, {"TWILIO_AUTH_TOKEN": auth_token}),
            patch(
                "app.routers.webhooks.twilio.forward_to_baby_mars",
                new_callable=AsyncMock,
            ) as mock_fwd,
        ):
            mock_fwd.return_value = True
            response = client.post(
                "/webhooks/twilio",
                data=params,
                headers={"X-Twilio-Signature": sig},
            )
            assert response.status_code == 200
            assert mock_fwd.called
            forwarded_event = mock_fwd.call_args[0][0]
            assert forwarded_event.event_type == "sms.received"
            assert forwarded_event.source_service == "twilio"
            assert forwarded_event.org_id == "AC_test_account"
            assert forwarded_event.raw_event_id == "SM_test_msg_001"
            assert forwarded_event.user_id == "+15551234567"


# ============================================================================
# Commit 7: Gmail push notification receiver
# ============================================================================


class TestGmailPushNotification:
    """Test Gmail Pub/Sub push notification receiver."""

    def _encode_pubsub_data(self, email: str, history_id: str) -> str:
        """Base64-encode a Gmail push notification payload."""
        import base64
        import json

        data = {"emailAddress": email, "historyId": history_id}
        return base64.b64encode(json.dumps(data).encode()).decode()

    def test_gmail_pubsub_token_verification(self, client: TestClient) -> None:
        """Gmail endpoint rejects requests with wrong token."""
        data_b64 = self._encode_pubsub_data("user@test.com", "100")

        with patch.dict(os.environ, {"GMAIL_PUBSUB_TOKEN": "correct_token"}):
            response = client.post(
                "/webhooks/gmail?token=wrong_token",
                json={
                    "message": {
                        "data": data_b64,
                        "messageId": "msg_001",
                    },
                    "subscription": "projects/test/subscriptions/gmail",
                },
            )
            assert response.status_code == 401

    def test_gmail_push_normalizes_notification(self, client: TestClient) -> None:
        """Valid Gmail push notification is normalized and forwarded."""
        data_b64 = self._encode_pubsub_data("user@test.com", "12345")

        with (
            patch.dict(os.environ, {"GMAIL_PUBSUB_TOKEN": ""}),
            patch(
                "app.routers.webhooks.gmail.forward_to_baby_mars",
                new_callable=AsyncMock,
            ) as mock_fwd,
            patch(
                "app.routers.webhooks.gmail._get_last_history_id",
                return_value=None,
            ),
            patch("app.routers.webhooks.gmail._set_last_history_id"),
        ):
            mock_fwd.return_value = True
            response = client.post(
                "/webhooks/gmail",
                json={
                    "message": {
                        "data": data_b64,
                        "messageId": "pubsub_msg_001",
                    },
                    "subscription": "projects/test/subscriptions/gmail",
                },
            )
            assert response.status_code == 200
            assert mock_fwd.called
            forwarded = mock_fwd.call_args[0][0]
            assert forwarded.event_type == "gmail.message.received"
            assert forwarded.source_service == "gmail"
            assert forwarded.org_id == "user@test.com"
            assert forwarded.user_id == "user@test.com"
            assert forwarded.payload["historyId"] == "12345"
            assert forwarded.payload["previousHistoryId"] is None

    def test_gmail_resolves_internal_tenant_identity(self, client: TestClient) -> None:
        """Gmail webhook uses credential-backed identity when available."""
        data_b64 = self._encode_pubsub_data("owner@test.com", "12346")

        with (
            patch.dict(os.environ, {"GMAIL_PUBSUB_TOKEN": ""}),
            patch(
                "app.routers.webhooks.gmail.resolve_webhook_identity",
                new_callable=AsyncMock,
            ) as mock_resolve,
            patch(
                "app.routers.webhooks.gmail.forward_to_baby_mars",
                new_callable=AsyncMock,
            ) as mock_fwd,
            patch(
                "app.routers.webhooks.gmail._get_last_history_id",
                return_value=None,
            ),
            patch("app.routers.webhooks.gmail._set_last_history_id"),
        ):
            mock_resolve.return_value = ("org_internal_google", "user_internal_google")
            mock_fwd.return_value = True

            response = client.post(
                "/webhooks/gmail",
                json={
                    "message": {
                        "data": data_b64,
                        "messageId": "pubsub_msg_003",
                    },
                    "subscription": "projects/test/subscriptions/gmail",
                },
            )

            assert response.status_code == 200
            forwarded = mock_fwd.call_args[0][0]
            assert forwarded.org_id == "org_internal_google"
            assert forwarded.user_id == "user_internal_google"

    def test_gmail_historyid_skip_regression(self, client: TestClient) -> None:
        """Gmail skips notifications with already-processed historyId."""
        data_b64 = self._encode_pubsub_data("user@test.com", "100")

        with (
            patch.dict(os.environ, {"GMAIL_PUBSUB_TOKEN": ""}),
            patch(
                "app.routers.webhooks.gmail._get_last_history_id",
                return_value="200",
            ),
            patch(
                "app.routers.webhooks.gmail.forward_to_baby_mars",
                new_callable=AsyncMock,
            ) as mock_fwd,
        ):
            response = client.post(
                "/webhooks/gmail",
                json={
                    "message": {
                        "data": data_b64,
                        "messageId": "pubsub_msg_002",
                    },
                    "subscription": "projects/test/subscriptions/gmail",
                },
            )
            assert response.status_code == 200
            # Should NOT have forwarded (historyId 100 <= 200)
            assert not mock_fwd.called


class TestGmailWatchRenewal:
    """Test Gmail watch renewal logic."""

    def test_gmail_watch_renewal_needed_no_watch(self) -> None:
        """Renewal needed when no watch exists."""
        from app.services.gmail_watch import check_watch_renewal_needed

        with patch("app.services.gmail_watch.redis_client") as mock_redis:
            mock_redis.get_cached_response.return_value = None

            result = check_watch_renewal_needed("org_test", "user_test", 1_000_000_000_000)
            assert result["needs_renewal"] is True
            assert result["reason"] == "no_watch_found"

    def test_gmail_watch_renewal_needed_expired(self) -> None:
        """Renewal needed when watch is expired."""
        from app.services.gmail_watch import check_watch_renewal_needed

        with patch("app.services.gmail_watch.redis_client") as mock_redis:
            # Watch expired at time 900 billion, current time is 1 trillion
            mock_redis.get_cached_response.return_value = {"expiration_ms": 900_000_000_000}

            result = check_watch_renewal_needed("org_test", "user_test", 1_000_000_000_000)
            assert result["needs_renewal"] is True
            assert result["reason"] == "expired"

    def test_gmail_watch_active(self) -> None:
        """No renewal needed when watch is active and not near expiry."""
        from app.services.gmail_watch import check_watch_renewal_needed

        with patch("app.services.gmail_watch.redis_client") as mock_redis:
            # Watch expires in 3 days (well within buffer)
            future_ms = 1_000_000_000_000 + 259_200_000
            mock_redis.get_cached_response.return_value = {"expiration_ms": future_ms}

            result = check_watch_renewal_needed("org_test", "user_test", 1_000_000_000_000)
            assert result["needs_renewal"] is False
            assert result["reason"] == "active"


# ============================================================================
# Commit 8: Delivery events for Tier 3 actions
# ============================================================================


class TestDeliveryEvents:
    """Test delivery event emission for Tier 3 actions."""

    def test_delivery_event_sent_for_tier_3_success(self, client: TestClient) -> None:
        """Tier 3 success emits delivery event with status=sent."""
        with (
            patch("app.routers.execute.get_capability") as mock_cap,
            patch(
                "app.services.execution.emit_delivery_event",
                new_callable=AsyncMock,
            ) as mock_emit,
        ):
            mock_cap.return_value = {
                "handler": lambda org_id, user_id, args: {"result": "sent"},
                "tool_name": "gmail.send",
                "service": "google",
                "credential_type": "user",
            }

            response = client.post(
                "/api/v1/execute",
                json={
                    "capability_key": "email.send",
                    "org_id": "org_tier3",
                    "user_id": "user_tier3",
                    "turn_id": "turn_delivery_success_001",
                    "args": {},
                    "metadata": {"verb_tier": 3, "proactive": True},
                },
            )

            assert response.status_code == 200
            assert response.json()["status"] == "success"

            # Delivery event should have been emitted
            assert mock_emit.called
            emitted_event = mock_emit.call_args[0][0]
            assert emitted_event.event_type == "delivery.email.send"
            assert emitted_event.source_service == "stargate"
            assert emitted_event.org_id == "org_tier3"
            assert emitted_event.raw_event_id == "turn_delivery_success_001:email.send"
            assert emitted_event.payload["status"] == "sent"
            assert emitted_event.payload["turn_id"] == "turn_delivery_success_001"
            assert emitted_event.payload["proactive"] is True
            assert isinstance(emitted_event.payload["duration_ms"], int)

    def test_delivery_event_sent_for_tier_3_failure(self, client: TestClient) -> None:
        """Tier 3 failure emits delivery event with status=failed."""

        def _raise_error(org_id: str, user_id: str, args: dict[str, Any]) -> None:
            msg = "Gmail API error"
            raise RuntimeError(msg)

        with (
            patch("app.routers.execute.get_capability") as mock_cap,
            patch(
                "app.services.execution.emit_delivery_event",
                new_callable=AsyncMock,
            ) as mock_emit,
        ):
            mock_cap.return_value = {
                "handler": _raise_error,
                "tool_name": "gmail.send",
                "service": "google",
                "credential_type": "user",
            }

            response = client.post(
                "/api/v1/execute",
                json={
                    "capability_key": "email.send",
                    "org_id": "org_tier3_fail",
                    "user_id": "user_tier3_fail",
                    "turn_id": "turn_delivery_fail_001",
                    "args": {},
                    "metadata": {"verb_tier": 3},
                },
            )

            assert response.status_code == 200
            assert response.json()["status"] == "error"

            # Delivery event should have been emitted with failed status
            assert mock_emit.called
            emitted_event = mock_emit.call_args[0][0]
            assert emitted_event.event_type == "delivery.email.send"
            assert emitted_event.payload["status"] == "failed"
            assert "error_code" in emitted_event.payload
            assert emitted_event.payload["turn_id"] == "turn_delivery_fail_001"

    def test_no_delivery_event_for_tier_0(self, client: TestClient) -> None:
        """Tier 0 (read-only) actions do NOT emit delivery events."""
        with (
            patch("app.routers.execute.get_capability") as mock_cap,
            patch(
                "app.services.execution.emit_delivery_event",
                new_callable=AsyncMock,
            ) as mock_emit,
        ):
            mock_cap.return_value = {
                "handler": lambda org_id, user_id, args: {"vendors": []},
                "tool_name": "quickbooks.list_vendors",
                "service": "quickbooks",
                "credential_type": "user",
            }

            response = client.post(
                "/api/v1/execute",
                json={
                    "capability_key": "vendor.list",
                    "org_id": "org_tier0",
                    "user_id": "user_tier0",
                    "turn_id": "turn_no_delivery_001",
                    "args": {},
                    "metadata": {"verb_tier": 0},
                },
            )

            assert response.status_code == 200
            assert response.json()["status"] == "success"

            # No delivery event for Tier 0
            assert not mock_emit.called
