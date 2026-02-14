"""
Tests for Autonomous Direction features (metadata passthrough, webhook forwarding,
delivery events).

Validates:
- metadata field on ToolExecutionRequest
- verb_tier logging and metric tagging
- Webhook forwarding infrastructure
- Delivery events for Tier 3 actions
"""

import contextlib
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

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
            # Verify verb_tier tag is present
            tags = success_calls[0].kwargs.get("tags", success_calls[0][1][0] if len(success_calls[0][1]) > 0 else [])
            # tags is the second positional arg or keyword arg
            call_args = success_calls[0]
            if call_args.kwargs.get("tags"):
                tag_list = call_args.kwargs["tags"]
            else:
                tag_list = call_args[0][1] if len(call_args[0]) > 1 else []
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
            call_args = success_calls[0]
            if call_args.kwargs.get("tags"):
                tag_list = call_args.kwargs["tags"]
            else:
                tag_list = call_args[0][1] if len(call_args[0]) > 1 else []
            assert any("verb_tier:unknown" in t for t in tag_list)
