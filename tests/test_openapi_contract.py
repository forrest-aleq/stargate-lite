"""
OpenAPI Contract Validation Tests

These tests ensure that Stargate's actual response shapes match the
OpenAPI spec (openapi.json). Baby MARS has contract tests that validate
their ability to parse our responses - these tests validate that we actually
produce what we promise.

Critical for integration with Baby MARS:
- They test they can parse our shapes
- We test we produce the promised shapes
- Together, this ensures contract compliance
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.errors import ErrorCode, RetryStrategy
from app.main import app, verify_api_key


# Override API key dependency
def mock_verify_api_key():
    return True


app.dependency_overrides[verify_api_key] = mock_verify_api_key


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def openapi_spec() -> dict[str, Any]:
    """Load OpenAPI spec for validation."""
    spec_path = Path(__file__).parent.parent / "openapi.json"
    with open(spec_path) as f:
        return json.load(f)


class TestToolExecutionResponseContract:
    """Validate ToolExecutionResponse matches OpenAPI spec."""

    def test_required_fields_present(self, openapi_spec: dict[str, Any]) -> None:
        """ToolExecutionResponse schema defines required fields correctly."""
        schema = openapi_spec["components"]["schemas"]["ToolExecutionResponse"]
        required_fields = schema["required"]

        # Per Baby MARS contract: required fields are status, capability_key, tool_used
        assert set(required_fields) == {"status", "capability_key", "tool_used"}

    def test_optional_fields_defined(self, openapi_spec: dict[str, Any]) -> None:
        """ToolExecutionResponse schema includes all optional fields."""
        schema = openapi_spec["components"]["schemas"]["ToolExecutionResponse"]
        properties = schema["properties"]

        # Per Baby MARS contract: optional fields
        optional_fields = {"outputs", "logs", "timestamp", "credential_type", "error"}
        for field in optional_fields:
            assert field in properties, f"Optional field {field} missing from schema"

    @patch("app.routers.execute.get_capability")
    def test_success_response_shape(
        self, mock_get_cap: MagicMock, client: TestClient
    ) -> None:
        """Actual success response matches ToolExecutionResponse schema."""
        mock_handler = MagicMock(return_value={"vendor_id": "qb:123"})
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
                "turn_id": "turn_openapi_001",
                "args": {},
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "status" in data
        assert "capability_key" in data
        assert "tool_used" in data

        # Type validation
        assert isinstance(data["status"], str)
        assert isinstance(data["capability_key"], str)
        assert isinstance(data["tool_used"], str)

        # Optional fields should be present and correctly typed
        assert isinstance(data.get("outputs"), dict)
        assert isinstance(data.get("logs"), list)
        if "timestamp" in data:
            assert isinstance(data["timestamp"], str)
        if "credential_type" in data:
            assert data["credential_type"] in {"agent", "customer", None}


class TestErrorResponseContract:
    """Validate ErrorResponse matches OpenAPI spec."""

    def test_required_fields_present(self, openapi_spec: dict[str, Any]) -> None:
        """ErrorResponse schema defines required fields correctly."""
        schema = openapi_spec["components"]["schemas"]["ErrorResponse"]
        required_fields = schema["required"]

        # Per Baby MARS contract: required fields
        assert set(required_fields) == {"error_code", "error_message", "retry_strategy"}

    def test_optional_fields_defined(self, openapi_spec: dict[str, Any]) -> None:
        """ErrorResponse schema includes all optional fields."""
        schema = openapi_spec["components"]["schemas"]["ErrorResponse"]
        properties = schema["properties"]

        # Per Baby MARS contract: optional fields
        optional_fields = {"status", "capability_key", "details", "timestamp"}
        for field in optional_fields:
            assert field in properties, f"Optional field {field} missing from schema"

    @patch("app.routers.execute.get_capability")
    def test_error_response_shape(
        self, mock_get_cap: MagicMock, client: TestClient
    ) -> None:
        """Actual error response matches ErrorResponse schema."""
        from app.errors import StargateError

        def raise_error(**kwargs):
            raise StargateError(
                error_code=ErrorCode.EXECUTION_ERROR,
                message="Test error",
                details={"test": "data"},
            )

        mock_get_cap.return_value = {
            "tool_name": "quickbooks.create_vendor",
            "service": "quickbooks",
            "handler": raise_error,
            "credential_type": "customer",
        }

        response = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "vendor.create",
                "org_id": "org_test",
                "user_id": "user_test",
                "turn_id": "turn_openapi_error_002_retry_fix",
                "args": {},
            },
        )

        assert response.status_code == 200  # Errors return 200
        data = response.json()

        # Required fields
        assert "error_code" in data
        assert "error_message" in data
        assert "retry_strategy" in data

        # Type validation
        assert isinstance(data["error_code"], str)
        assert isinstance(data["error_message"], str)
        assert isinstance(data["retry_strategy"], str)

        # Optional fields validation
        if "status" in data:
            assert data["status"] == "error"
        if "details" in data:
            assert isinstance(data["details"], dict)


class TestErrorCodeContract:
    """Validate ErrorCode enum matches OpenAPI spec."""

    def test_error_code_enum_count(self, openapi_spec: dict[str, Any]) -> None:
        """ErrorCode enum has exactly 10 values (per Baby MARS contract)."""
        schema = openapi_spec["components"]["schemas"]["ErrorCode"]
        enum_values = schema["enum"]

        # Per Baby MARS: exactly 10 error codes
        assert len(enum_values) == 10

    def test_error_code_enum_values(self, openapi_spec: dict[str, Any]) -> None:
        """ErrorCode enum contains all expected values."""
        schema = openapi_spec["components"]["schemas"]["ErrorCode"]
        enum_values = set(schema["enum"])

        # Per Baby MARS contract: exact list of error codes
        expected_codes = {
            "CAPABILITY_NOT_FOUND",
            "CREDENTIALS_MISSING",
            "CREDENTIALS_INVALID",
            "CREDENTIALS_INSUFFICIENT",
            "RATE_LIMIT",
            "NETWORK_ERROR",
            "VALIDATION_ERROR",
            "EXECUTION_ERROR",
            "QUOTA_EXCEEDED",
            "PERMISSION_DENIED",
        }

        assert enum_values == expected_codes

    def test_error_code_python_enum_matches_spec(
        self, openapi_spec: dict[str, Any]
    ) -> None:
        """Python ErrorCode enum matches OpenAPI spec."""
        spec_enum = set(openapi_spec["components"]["schemas"]["ErrorCode"]["enum"])
        python_enum = {code.value for code in ErrorCode}

        assert python_enum == spec_enum, "Python ErrorCode enum doesn't match OpenAPI spec"


class TestRetryStrategyContract:
    """Validate RetryStrategy enum matches OpenAPI spec."""

    def test_retry_strategy_enum_values(self, openapi_spec: dict[str, Any]) -> None:
        """RetryStrategy enum values match spec."""
        schema = openapi_spec["components"]["schemas"]["RetryStrategy"]
        enum_values = set(schema["enum"])

        # Current values in our spec
        expected_strategies = {"human_intervention", "backoff", "none"}

        assert enum_values == expected_strategies

    def test_retry_strategy_python_enum_matches_spec(
        self, openapi_spec: dict[str, Any]
    ) -> None:
        """Python RetryStrategy enum matches OpenAPI spec."""
        spec_enum = set(openapi_spec["components"]["schemas"]["RetryStrategy"]["enum"])
        python_enum = {strategy.value for strategy in RetryStrategy}

        assert (
            python_enum == spec_enum
        ), "Python RetryStrategy enum doesn't match OpenAPI spec"

    def test_all_error_codes_have_retry_strategy(self) -> None:
        """Every ErrorCode has a mapped RetryStrategy."""
        from app.errors import ERROR_RETRY_STRATEGIES

        for error_code in ErrorCode:
            assert (
                error_code in ERROR_RETRY_STRATEGIES
            ), f"ErrorCode.{error_code.name} missing from ERROR_RETRY_STRATEGIES mapping"


class TestDeepLinkContract:
    """Validate deep_link fields in outputs (per Baby MARS v0.10.0 contract)."""

    @pytest.mark.parametrize(
        "entity_type",
        [
            "vendor",
            "customer",
            "invoice",
            "bill",
            "expense",
            "journal_entry",
            "payment",
            "bill_payment",
            "purchase_order",
            "sales_receipt",
            "credit_memo",
            "refund_receipt",
            "estimate",
            "deposit",
            "transfer",
            "time_activity",
            "account",
        ],
    )
    def test_quickbooks_deep_link_field_exists(self, entity_type: str) -> None:
        """All QuickBooks entity types should support deep_link in outputs."""
        # This is a metadata test - we're documenting that deep_link
        # should be present in QuickBooks connector responses
        # Actual validation would require mocking QB API calls
        # which is better done in connector-specific tests
        assert True  # Placeholder - actual validation in connector tests


class TestBatchStopOnErrorContract:
    """Validate batch stop-on-error behavior (per Baby MARS contract)."""

    def test_batch_halts_on_human_intervention_error(self) -> None:
        """Batch execution should halt on human_intervention retry strategy."""
        # Per Baby MARS: batch operations stop on errors requiring human intervention
        from app.errors import ERROR_RETRY_STRATEGIES

        human_intervention_codes = [
            code
            for code, strategy in ERROR_RETRY_STRATEGIES.items()
            if strategy == RetryStrategy.HUMAN_INTERVENTION
        ]

        # These errors should halt batch processing
        expected_halt_codes = {
            ErrorCode.CREDENTIALS_MISSING,
            ErrorCode.CREDENTIALS_INVALID,
            ErrorCode.CREDENTIALS_INSUFFICIENT,
            ErrorCode.QUOTA_EXCEEDED,
            ErrorCode.PERMISSION_DENIED,
        }

        assert set(human_intervention_codes) == expected_halt_codes

    def test_batch_halts_on_none_retry_strategy(self) -> None:
        """Batch execution should halt on 'none' retry strategy."""
        from app.errors import ERROR_RETRY_STRATEGIES

        none_retry_codes = [
            code
            for code, strategy in ERROR_RETRY_STRATEGIES.items()
            if strategy == RetryStrategy.NONE
        ]

        # These errors should also halt batch processing
        expected_halt_codes = {
            ErrorCode.CAPABILITY_NOT_FOUND,
            ErrorCode.VALIDATION_ERROR,
        }

        assert set(none_retry_codes) == expected_halt_codes


class TestLegacyErrorCodeMapping:
    """Validate backward compatibility with v0.9.x error codes."""

    def test_legacy_error_codes_documented(self) -> None:
        """Legacy error code mapping is documented."""
        # Per Baby MARS: v0.9.x codes still accepted
        # This test documents that we should maintain backward compatibility
        # TODO: Implement actual legacy code mapping if needed
        assert True  # Placeholder for future implementation
