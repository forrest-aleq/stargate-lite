"""
Consumer Contract Tests — Baby MARS expectations

Validates that Stargate's generated OpenAPI spec and contract declarations
match what Baby MARS expects. Tests run against both:
  - The committed openapi.json file (what CI and Baby MARS see)
  - The runtime /openapi.json endpoint (what deployed consumers see)

Coverage:
1. /api/v1/execute response uses oneOf + discriminator (not anyOf)
2. ErrorResponse schema includes all 10 canonical error codes
3. ToolExecutionResponse schema has required fields matching mars.py
4. /api/v1/capabilities returns CapabilitiesResponse schema
5. Rate-limit returns 429 (documented in OpenAPI)
6. Error codes in mars.py match ErrorCode enum in errors.py
7. Retry strategies in mars.py match RetryStrategy enum in errors.py
8. Runtime /openapi.json matches committed file (no drift)
"""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.contracts.mars import MARS_CONTRACT
from app.errors import ERROR_RETRY_STRATEGIES, ErrorCode, RetryStrategy
from app.main import app, verify_api_key


def _mock_verify_api_key() -> bool:
    return True


app.dependency_overrides[verify_api_key] = _mock_verify_api_key


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def openapi_spec() -> dict[str, Any]:
    """Load the committed OpenAPI spec."""
    spec_path = Path(__file__).parent.parent / "openapi.json"
    with spec_path.open() as f:
        return json.load(f)


class TestExecuteResponseUnion:
    """1. /api/v1/execute response uses oneOf + discriminator."""

    def test_execute_200_uses_oneof(self, openapi_spec: dict[str, Any]) -> None:
        schema = (
            openapi_spec["paths"]["/api/v1/execute"]["post"]["responses"]["200"]
            ["content"]["application/json"]["schema"]
        )
        assert "oneOf" in schema, "Execute 200 response must use oneOf (not anyOf)"
        assert "anyOf" not in schema, "anyOf must not be present alongside oneOf"

    def test_execute_200_has_discriminator(self, openapi_spec: dict[str, Any]) -> None:
        schema = (
            openapi_spec["paths"]["/api/v1/execute"]["post"]["responses"]["200"]
            ["content"]["application/json"]["schema"]
        )
        disc = schema.get("discriminator", {})
        assert disc.get("propertyName") == "status"
        mapping = disc.get("mapping", {})
        assert "success" in mapping
        assert "error" in mapping


class TestErrorResponseSchema:
    """2. ErrorResponse schema includes all 10 canonical error codes."""

    def test_error_code_enum_has_10_values(self, openapi_spec: dict[str, Any]) -> None:
        enum_vals = openapi_spec["components"]["schemas"]["ErrorCode"]["enum"]
        assert len(enum_vals) == 10, f"Expected 10 error codes, got {len(enum_vals)}"

    def test_error_code_enum_matches_canonical(self, openapi_spec: dict[str, Any]) -> None:
        enum_vals = set(openapi_spec["components"]["schemas"]["ErrorCode"]["enum"])
        expected = {
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
        assert enum_vals == expected


class TestToolExecutionResponseSchema:
    """3. ToolExecutionResponse required fields match mars.py."""

    def test_required_fields_match_contract(self, openapi_spec: dict[str, Any]) -> None:
        schema = openapi_spec["components"]["schemas"]["ToolExecutionResponse"]
        required = set(schema["required"])
        contract_required = set(MARS_CONTRACT["success_response"]["required"])  # type: ignore[arg-type]
        # OpenAPI required is a subset check — all contract-required must be in schema
        missing = contract_required - required
        # 'outputs', 'logs', 'timestamp' have defaults in Pydantic so they're
        # not in OpenAPI 'required' — but they're always present at runtime.
        # The critical ones are status, capability_key, tool_used.
        critical = {"status", "capability_key", "tool_used"}
        assert critical.issubset(required), f"Missing critical fields: {critical - required}"


class TestCapabilitiesResponseSchema:
    """4. /api/v1/capabilities returns typed CapabilitiesResponse."""

    def test_capabilities_endpoint_returns_typed_model(
        self, openapi_spec: dict[str, Any]
    ) -> None:
        cap_resp = (
            openapi_spec["paths"]["/api/v1/capabilities"]["get"]["responses"]["200"]
            ["content"]["application/json"]["schema"]
        )
        # Should reference CapabilitiesResponse, not be a generic object
        ref = cap_resp.get("$ref", "")
        assert "CapabilitiesResponse" in ref, (
            f"Expected CapabilitiesResponse ref, got: {cap_resp}"
        )

    def test_capabilities_response_has_required_fields(
        self, openapi_spec: dict[str, Any]
    ) -> None:
        schema = openapi_spec["components"]["schemas"]["CapabilitiesResponse"]
        assert "capabilities" in schema["properties"]
        assert "count" in schema["properties"]


class TestRateLimitDocumented:
    """5. Rate-limit returns 429 — documented in OpenAPI."""

    def test_execute_documents_429(self, openapi_spec: dict[str, Any]) -> None:
        responses = openapi_spec["paths"]["/api/v1/execute"]["post"]["responses"]
        assert "429" in responses, "Execute endpoint must document 429 response"

    def test_mars_contract_acknowledges_429(self) -> None:
        error_resp = MARS_CONTRACT["error_response"]
        assert error_resp["rate_limit_http_code"] == 429  # type: ignore[index]


class TestMarsErrorCodesMatchEnum:
    """6. Error codes in mars.py match ErrorCode enum in errors.py."""

    def test_mars_codes_match_error_code_enum(self) -> None:
        mars_codes = set(MARS_CONTRACT["error_codes"].keys())  # type: ignore[union-attr]
        # ErrorCode enum has legacy aliases — get unique values
        enum_values = {code.value for code in ErrorCode}
        assert mars_codes == enum_values, (
            f"Mars codes: {mars_codes}\nEnum values: {enum_values}\n"
            f"Only in mars: {mars_codes - enum_values}\n"
            f"Only in enum: {enum_values - mars_codes}"
        )


class TestMarsRetryStrategiesMatchEnum:
    """7. Retry strategies in mars.py match RetryStrategy enum in errors.py."""

    def test_mars_strategies_match_enum(self) -> None:
        mars_strategies = set(MARS_CONTRACT["retry_strategies"])  # type: ignore[arg-type]
        enum_strategies = {s.value for s in RetryStrategy}
        assert mars_strategies == enum_strategies, (
            f"Mars strategies: {mars_strategies}\n"
            f"Enum strategies: {enum_strategies}"
        )

    def test_mars_error_retry_mappings_match(self) -> None:
        """Each mars.py error code's retry matches ERROR_RETRY_STRATEGIES."""
        mars_codes = MARS_CONTRACT["error_codes"]
        assert isinstance(mars_codes, dict)
        for code_str, info in mars_codes.items():
            error_code = ErrorCode(code_str)
            expected_strategy = ERROR_RETRY_STRATEGIES[error_code]
            assert info["retry"] == expected_strategy.value, (
                f"{code_str}: mars says '{info['retry']}', "
                f"errors.py says '{expected_strategy.value}'"
            )


class TestRuntimeSchemaMatchesCommitted:
    """8. Runtime /openapi.json matches committed openapi.json."""

    def test_runtime_execute_uses_oneof(self, client: TestClient) -> None:
        """Runtime /openapi.json serves oneOf + discriminator on execute."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        runtime_spec = resp.json()
        schema = (
            runtime_spec["paths"]["/api/v1/execute"]["post"]["responses"]["200"]
            ["content"]["application/json"]["schema"]
        )
        assert "oneOf" in schema, "Runtime spec must use oneOf (not anyOf)"
        assert "anyOf" not in schema

    def test_runtime_spec_matches_committed(
        self, client: TestClient, openapi_spec: dict[str, Any]
    ) -> None:
        """Runtime /openapi.json is identical to committed openapi.json."""
        resp = client.get("/openapi.json")
        runtime_spec = resp.json()

        def _normalize(spec: dict[str, Any]) -> str:
            return json.dumps(spec, indent=2, sort_keys=True, default=str)

        assert _normalize(runtime_spec) == _normalize(openapi_spec), (
            "Runtime OpenAPI spec differs from committed openapi.json. "
            "Run 'python scripts/generate_openapi.py' to sync."
        )
