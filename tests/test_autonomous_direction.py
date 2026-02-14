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
            patch("app.routers.webhooks.base.BABY_MARS_WEBHOOK_URL", "http://mars.test/webhooks/stargate"),
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
        """Mock HTTP failure, verify 3 attempts."""
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
            patch("app.routers.webhooks.base.BABY_MARS_WEBHOOK_URL", "http://mars.test/webhooks/stargate"),
            patch("app.routers.webhooks.base._get_forward_session") as mock_session_fn,
            patch("app.routers.webhooks.base.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_session = MagicMock()
            mock_session.post.return_value = mock_response
            mock_session_fn.return_value = mock_session

            from app.routers.webhooks.base import forward_to_baby_mars

            result = asyncio.get_event_loop().run_until_complete(forward_to_baby_mars(event))
            assert result is False
            assert mock_session.post.call_count == 3


# ============================================================================
# Commit 5: Stripe + QBO + Xero webhook receivers
# ============================================================================


class TestStripeWebhook:
    """Test Stripe webhook receiver."""

    def _make_stripe_signature(self, payload: bytes, secret: str, timestamp: str | None = None) -> str:
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
            patch("app.routers.webhooks.stripe.forward_to_baby_mars", new_callable=AsyncMock) as mock_fwd,
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


class TestQBOWebhook:
    """Test QuickBooks Online webhook receiver."""

    def test_qbo_challenge_response(self, client: TestClient) -> None:
        """QBO verification challenge returns correct HMAC."""
        import hashlib
        import hmac as _hmac

        verifier = "test_verifier_token"
        challenge = "challenge_abc"

        expected_hash = _hmac.new(
            verifier.encode(), challenge.encode(), hashlib.sha256
        ).hexdigest()

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
                        "entities": [
                            {"name": "Invoice", "id": "inv_001", "operation": "Create"}
                        ]
                    },
                }
            ]
        }
        import json

        payload_bytes = json.dumps(payload_dict).encode()
        sig = _hmac.new(verifier.encode(), payload_bytes, hashlib.sha256).hexdigest()

        with (
            patch.dict(os.environ, {"QBO_WEBHOOK_VERIFIER_TOKEN": verifier}),
            patch("app.routers.webhooks.quickbooks.forward_to_baby_mars", new_callable=AsyncMock) as mock_fwd,
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
