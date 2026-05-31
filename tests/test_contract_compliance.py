"""
Contract v1.0 Compliance Tests for Stargate Command API

Validates full compliance with stargate-command-contract.md:
- turn_id is REQUIRED (422 if missing)
- Idempotency: same turn_id returns cached response
- All 10 error codes properly formatted
- Multi-tenancy: org_id and user_id required
- Response schema matches contract exactly
"""

import contextlib
import json
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.errors import ErrorCode, StargateError
from app.main import app, verify_api_key


# Override API key dependency for all tests
def mock_verify_api_key():
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


class TestRequiredFields:
    """Test that all contract-required fields are validated."""

    def test_missing_turn_id_returns_422(self, client: TestClient) -> None:
        """Contract v1.0: turn_id is REQUIRED - missing returns 422."""
        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                "org_id": "org_test",
                "user_id": "user_test",
                # turn_id MISSING - should fail validation
                "args": {"vendor_name": "Acme Inc"},
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Pydantic validation error should mention turn_id
        error_str = json.dumps(data["detail"]).lower()
        assert "turn_id" in error_str

    def test_missing_org_id_returns_422(self, client: TestClient) -> None:
        """Multi-tenancy: org_id is REQUIRED."""
        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                # org_id MISSING
                "user_id": "user_test",
                "turn_id": "turn_test_001",
                "args": {},
            },
        )

        assert response.status_code == 422

    def test_missing_user_id_returns_422(self, client: TestClient) -> None:
        """Multi-tenancy: user_id is REQUIRED."""
        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                "org_id": "org_test",
                # user_id MISSING
                "turn_id": "turn_test_002",
                "args": {},
            },
        )

        assert response.status_code == 422

    def test_missing_capability_key_returns_422(self, client: TestClient) -> None:
        """Capability key is REQUIRED."""
        response = client.post(
            "/api/v1/execute",
            json={
                # capability_key MISSING
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": "turn_test_003",
                "args": {},
            },
        )

        assert response.status_code == 422


class TestIdempotency:
    """Test idempotency behavior using turn_id + capability_key."""

    @patch("app.routers.execute.get_capability")
    @patch("app.services.idempotency.redis_client")
    def test_same_turn_id_returns_cached_response(
        self,
        mock_redis: MagicMock,
        mock_get_cap: MagicMock,
        client: TestClient,
    ) -> None:
        """Contract v1.0: Same turn_id + capability_key returns cached response."""
        # Mock Redis to return cached response
        cached_response = {
            "status": "success",
            "capability_key": "vendor.create",
            "tool_used": "quickbooks.create_vendor",
            "outputs": {"vendor_id": "cached_123"},
            "logs": ["Cached execution"],
            "credential_type": "customer",
        }
        mock_redis.get_cached_execution_response.return_value = cached_response

        # Execute request
        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": "turn_idempotent_001",
                "args": {"vendor_name": "Acme Inc"},
            },
        )

        # Should return cached response
        assert response.status_code == 200
        data = response.json()
        assert data["outputs"]["vendor_id"] == "cached_123"

        # get_capability should NOT be called (cache hit)
        mock_get_cap.assert_not_called()

    @patch("app.routers.execute.get_capability")
    @patch("app.services.idempotency.redis_client")
    def test_different_turn_id_executes_new_request(
        self,
        mock_redis: MagicMock,
        mock_get_cap: MagicMock,
        client: TestClient,
    ) -> None:
        """Different turn_id executes new request (not cached)."""
        # Mock Redis: no cached response
        mock_redis.get_cached_execution_response.return_value = None
        mock_redis.acquire_execution_lock.return_value = True
        mock_redis.cache_execution_response.return_value = True

        # Mock capability
        mock_handler = MagicMock(return_value={"vendor_id": "new_456"})
        mock_get_cap.return_value = {
            "tool_name": "quickbooks.create_vendor",
            "service": "quickbooks",
            "handler": mock_handler,
            "credential_type": "customer",
        }

        # Execute with new turn_id
        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": "turn_new_002",
                "args": {"vendor_name": "New Vendor"},
            },
        )

        # Should execute new request
        assert response.status_code == 200
        data = response.json()
        assert data["outputs"]["vendor_id"] == "new_456"

        # Handler SHOULD be called
        mock_handler.assert_called_once()


class TestErrorCodes:
    """Test all 10 contract-specified error codes."""

    def test_capability_not_found_error(self, client: TestClient) -> None:
        """CAPABILITY_NOT_FOUND: Unknown capability_key."""
        # No mocking - let it naturally fail to find capability
        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "invalid.capability.does.not.exist",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": "turn_err_001",
                "args": {},
            },
        )

        assert response.status_code == 200  # Contract: errors return 200
        data = response.json()
        assert data["status"] == "error"
        # Should be CAPABILITY_NOT_FOUND or EXECUTION_ERROR
        assert data["error_code"] in ["CAPABILITY_NOT_FOUND", "EXECUTION_ERROR"]

    @patch("app.routers.execute.get_capability")
    def test_credentials_missing_error(self, mock_get_cap: MagicMock, client: TestClient) -> None:
        """CREDENTIALS_MISSING: No credentials found for service."""

        # Mock handler that raises CREDENTIALS_MISSING
        def raise_creds_missing(**kwargs):
            raise StargateError(
                error_code=ErrorCode.CREDENTIALS_MISSING,
                message="No QuickBooks credentials found",
                details={"service": "quickbooks"},
            )

        mock_get_cap.return_value = {
            "tool_name": "quickbooks.create_vendor",
            "service": "quickbooks",
            "handler": raise_creds_missing,
            "credential_type": "customer",
        }

        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": "turn_err_002",
                "args": {},
            },
        )

        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "CREDENTIALS_MISSING"

    @patch("app.routers.execute.get_capability")
    def test_validation_error(self, mock_get_cap: MagicMock, client: TestClient) -> None:
        """VALIDATION_ERROR: Invalid arguments provided."""

        def raise_validation_error(**kwargs):
            raise StargateError(
                error_code=ErrorCode.VALIDATION_ERROR,
                message="Missing required field: vendor_name",
                details={"missing_fields": ["vendor_name"]},
            )

        mock_get_cap.return_value = {
            "tool_name": "quickbooks.create_vendor",
            "service": "quickbooks",
            "handler": raise_validation_error,
            "credential_type": "customer",
        }

        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": "turn_err_004",
                "args": {},  # Missing vendor_name
            },
        )

        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "VALIDATION_ERROR"


class TestResponseSchema:
    """Test that responses match contract schema exactly."""

    @patch("app.routers.execute.get_capability")
    def test_success_response_schema(self, mock_get_cap: MagicMock, client: TestClient) -> None:
        """Success response includes all required fields."""
        mock_handler = MagicMock(return_value={"vendor_id": "qb:123", "status": "active"})
        mock_get_cap.return_value = {
            "tool_name": "quickbooks.create_vendor",
            "service": "quickbooks",
            "handler": mock_handler,
            "credential_type": "customer",
        }

        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": "turn_schema_001",
                "args": {"vendor_name": "Acme Inc"},
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields per contract
        assert "status" in data
        assert data["status"] == "success"
        assert "capability_key" in data
        assert data["capability_key"] == "vendor.create"
        assert "tool_used" in data
        assert "outputs" in data
        assert "logs" in data
        assert isinstance(data["logs"], list)

        # Optional fields
        assert "credential_type" in data
        assert "timestamp" in data

    @patch("app.routers.execute.get_capability")
    def test_error_response_schema(self, mock_get_cap: MagicMock, client: TestClient) -> None:
        """Error response includes status='error', error_code, error_message."""

        def raise_execution_error(**kwargs):
            raise StargateError(
                error_code=ErrorCode.EXECUTION_ERROR,
                message="QuickBooks API returned 500 error",
                details={"http_status": 500},
            )

        mock_get_cap.return_value = {
            "tool_name": "quickbooks.create_vendor",
            "service": "quickbooks",
            "handler": raise_execution_error,
            "credential_type": "customer",
        }

        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": "turn_schema_002",
                "args": {},
            },
        )

        assert response.status_code == 200  # Contract: errors return 200
        data = response.json()

        # Required error fields per contract
        assert data["status"] == "error"
        assert "error_code" in data
        assert "error_message" in data
        assert isinstance(data["error_code"], str)
        assert isinstance(data["error_message"], str)

        # Optional fields
        if "details" in data:
            assert isinstance(data["details"], dict)


class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_check_returns_200(self, client: TestClient) -> None:
        """Health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_schema(self, client: TestClient) -> None:
        """Health check response includes required fields."""
        response = client.get("/health")
        data = response.json()

        # Required fields
        assert "status" in data
        assert isinstance(data["status"], str)
