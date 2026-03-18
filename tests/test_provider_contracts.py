"""
Provider Contract Drift Tests

Validates that the live FastAPI app conforms to the locked provider contracts.
If someone adds/removes an endpoint, changes error codes, or alters response
shapes — these tests fail.

These are NOT duplicates of test_contract_compliance.py (which tests behavior).
These test that the locked contract data structures match the live app.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.contracts.mars import MARS_CONTRACT
from app.contracts.n3 import N3_CONTRACT
from app.errors import ERROR_RETRY_STRATEGIES, ErrorCode, RetryStrategy
from app.main import app, verify_api_key
from app.models import ErrorResponse, ToolExecutionRequest, ToolExecutionResponse


# Override API key dependency for all tests
def mock_verify_api_key() -> bool:
    return True


app.dependency_overrides[verify_api_key] = mock_verify_api_key


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ── Helpers ────────────────────────────────────────────────────────────


def _normalise_path(path: str) -> str:
    """Convert contract path like /oauth/{provider}/authorize to a regex-friendly form."""
    # FastAPI registers /oauth/quickbooks/authorize, etc.
    # We just need to check the prefix pattern exists in the route table.
    return path.split("{")[0] if "{" in path else path


def _find_route(method: str, path: str) -> bool:
    """Check if a route with the given method and path exists on the app."""
    normalised = _normalise_path(path)
    for route in app.routes:
        route_path: str = getattr(route, "path", "")
        route_methods: set[str] = getattr(route, "methods", set())
        if method.upper() in route_methods and route_path.startswith(normalised):
            return True
        # For path-param routes, check that the pattern matches
        if "{" in path:
            # e.g. /oauth/{provider}/authorize -> /oauth/quickbooks/authorize
            prefix = path.split("{")[0]
            suffix = path.split("}")[-1] if "}" in path else ""
            if (
                method.upper() in route_methods
                and route_path.startswith(prefix)
                and route_path.endswith(suffix)
            ):
                return True
    return False


# ═══════════════════════════════════════════════════════════════════════
# N3 CONTRACT TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestN3ContractEndpoints:
    """Every endpoint in N3_CONTRACT must exist on the FastAPI app."""

    def test_n3_contract_version(self) -> None:
        assert N3_CONTRACT["version"] == "1.1.0"

    def test_n3_health_endpoint_exists(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_n3_connectors_status_exists(self, client: TestClient) -> None:
        assert _find_route("POST", "/api/v1/connectors/status")

    def test_n3_credentials_status_exists(self, client: TestClient) -> None:
        assert _find_route("POST", "/api/v1/credentials/status")

    def test_n3_credentials_metadata_exists(self, client: TestClient) -> None:
        assert _find_route("GET", "/api/v1/credentials/metadata")

    def test_n3_credentials_revoke_exists(self, client: TestClient) -> None:
        assert _find_route("POST", "/api/v1/credentials/revoke")

    def test_n3_oauth_authorize_routes_exist(self) -> None:
        """At least one OAuth authorize route must exist."""
        found = False
        for route in app.routes:
            path: str = getattr(route, "path", "")
            methods: set[str] = getattr(route, "methods", set())
            if "/oauth/" in path and path.endswith("/authorize") and "GET" in methods:
                found = True
                break
        assert found, "No /oauth/{provider}/authorize GET route found"

    def test_n3_oauth_callback_routes_exist(self) -> None:
        """At least one OAuth callback route must exist."""
        found = False
        for route in app.routes:
            path: str = getattr(route, "path", "")
            methods: set[str] = getattr(route, "methods", set())
            if "/oauth/" in path and path.endswith("/callback") and "GET" in methods:
                found = True
                break
        assert found, "No /oauth/{provider}/callback GET route found"

    def test_n3_all_endpoints_accounted_for(self) -> None:
        """Every endpoint listed in the N3 contract must resolve to a route."""
        endpoints: list[dict[str, Any]] = N3_CONTRACT["endpoints"]  # type: ignore[assignment]
        for ep in endpoints:
            method: str = ep["method"]
            path: str = ep["path"]
            assert _find_route(
                method, path
            ), f"N3 contract endpoint {method} {path} not found on app"

    def test_n3_denied_execute_not_accessible(self) -> None:
        """N3 denied endpoints should conceptually not be in the N3 contract."""
        denied: list[str] = N3_CONTRACT["denied"]  # type: ignore[assignment]
        endpoint_paths = [
            f"{ep['method']} {ep['path']}"  # type: ignore[index]
            for ep in N3_CONTRACT["endpoints"]  # type: ignore[union-attr]
        ]
        for d in denied:
            # Strip wildcard for comparison
            pattern = d.replace("/*", "")
            for ep_path in endpoint_paths:
                assert not ep_path.startswith(
                    pattern
                ), f"Denied endpoint '{d}' found in N3 contract endpoints"


# ═══════════════════════════════════════════════════════════════════════
# MARS CONTRACT TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestMarsContractEndpoints:
    """All MARS endpoints must exist on the FastAPI app."""

    def test_mars_contract_version(self) -> None:
        assert MARS_CONTRACT["version"] == "1.1.0"

    def test_mars_capability_catalog_exists(self) -> None:
        """Contract must expose a capability catalog via get_capability_catalog()."""
        from app.contracts.mars import get_capability_catalog

        catalog = get_capability_catalog()
        assert len(catalog) > 0, "Catalog must have at least one service"
        total_keys = sum(len(keys) for keys in catalog.values())
        assert total_keys > 0, "Catalog must have capability keys"

    def test_mars_catalog_matches_registry(self) -> None:
        """Every registry key must appear in the contract catalog."""
        from app.contracts.mars import get_capability_catalog
        from app.registry import CAPABILITY_REGISTRY

        catalog = get_capability_catalog()
        catalog_keys = {k for keys in catalog.values() for k in keys}
        registry_keys = set(CAPABILITY_REGISTRY.keys())
        missing = registry_keys - catalog_keys
        assert not missing, f"Registry keys missing from contract: {missing}"
        extra = catalog_keys - registry_keys
        assert not extra, f"Contract keys not in registry: {extra}"

    def test_mars_execute_endpoint_exists(self, client: TestClient) -> None:
        assert _find_route("POST", "/api/v1/execute")

    def test_mars_capabilities_endpoint_exists(self, client: TestClient) -> None:
        resp = client.get("/api/v1/capabilities")
        assert resp.status_code == 200

    def test_mars_schemas_endpoint_exists(self, client: TestClient) -> None:
        assert _find_route("GET", "/api/v1/schemas/{capability_key}")

    def test_mars_health_endpoint_exists(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_mars_all_endpoints_accounted_for(self) -> None:
        """Every endpoint listed in the MARS contract must resolve to a route."""
        endpoints: list[dict[str, Any]] = MARS_CONTRACT["endpoints"]  # type: ignore[assignment]
        for ep in endpoints:
            method: str = ep["method"]
            path: str = ep["path"]
            assert _find_route(
                method, path
            ), f"MARS contract endpoint {method} {path} not found on app"


class TestMarsExecuteRequest:
    """Execute request contract: required/optional field validation."""

    def test_required_fields_match_model(self) -> None:
        """ToolExecutionRequest must have all fields listed as required."""
        execute_req: dict[str, Any] = MARS_CONTRACT["execute_request"]  # type: ignore[assignment]
        required: list[str] = execute_req["required"]
        model_required = {
            name for name, field in ToolExecutionRequest.model_fields.items() if field.is_required()
        }
        for field_name in required:
            assert field_name in model_required, (
                f"Contract requires '{field_name}' but ToolExecutionRequest "
                f"does not mark it as required"
            )

    def test_optional_fields_exist_on_model(self) -> None:
        """All optional fields in the contract must exist on the model."""
        execute_req: dict[str, Any] = MARS_CONTRACT["execute_request"]  # type: ignore[assignment]
        optional: list[str] = execute_req["optional"]
        model_fields = set(ToolExecutionRequest.model_fields.keys())
        for field_name in optional:
            assert (
                field_name in model_fields
            ), f"Contract optional field '{field_name}' not found on ToolExecutionRequest"

    def test_missing_required_fields_return_422(self, client: TestClient) -> None:
        """Omitting any required field should return 422."""
        execute_req: dict[str, Any] = MARS_CONTRACT["execute_request"]  # type: ignore[assignment]
        full_body = {
            "capability_key": "test.cap",
            "org_id": "org_1",
            "user_id": "user_1",
            "turn_id": "turn_1",
        }
        for field in execute_req["required"]:
            body = {k: v for k, v in full_body.items() if k != field}
            resp = client.post("/api/v1/execute", json=body)
            assert (
                resp.status_code == 422
            ), f"Missing '{field}' should return 422, got {resp.status_code}"


class TestMarsSuccessResponse:
    """Success response must have all required fields from the contract."""

    def test_success_response_required_fields_on_model(self) -> None:
        success: dict[str, Any] = MARS_CONTRACT["success_response"]  # type: ignore[assignment]
        model_fields = set(ToolExecutionResponse.model_fields.keys())
        for field_name in success["required"]:
            assert (
                field_name in model_fields
            ), f"Contract success field '{field_name}' not on ToolExecutionResponse"

    def test_success_response_optional_fields_on_model(self) -> None:
        success: dict[str, Any] = MARS_CONTRACT["success_response"]  # type: ignore[assignment]
        model_fields = set(ToolExecutionResponse.model_fields.keys())
        for field_name in success["optional"]:
            assert (
                field_name in model_fields
            ), f"Contract optional field '{field_name}' not on ToolExecutionResponse"

    @patch("app.routers.execute.get_capability")
    @patch("app.routers.execute.execute_handler", new_callable=AsyncMock)
    @patch("app.routers.execute.rate_limiter")
    def test_live_success_response_shape(
        self,
        mock_limiter: MagicMock,
        mock_exec: AsyncMock,
        mock_cap: MagicMock,
        client: TestClient,
    ) -> None:
        """A real success response must include every required field."""
        mock_limiter.check_rate_limit.return_value = (
            True,
            {"limit": 100, "remaining": 99, "reset_at": 9999999999},
        )
        mock_cap.return_value = {
            "handler": lambda *a: {},
            "tool_name": "test.tool",
            "service": "test",
            "requires_oauth": False,
            "credential_type": "agent",
        }
        mock_exec.return_value = ({"result": "ok"}, 0.1)

        resp = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "test.cap",
                "org_id": "org_1",
                "user_id": "user_1",
                "turn_id": "turn_success_shape",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        success: dict[str, Any] = MARS_CONTRACT["success_response"]  # type: ignore[assignment]
        for field_name in success["required"]:
            assert (
                field_name in data
            ), f"Required success field '{field_name}' missing from live response"
        assert data["status"] == success["status_value"]


class TestMarsErrorResponse:
    """Error response must have all required fields from the contract."""

    def test_error_response_required_fields_on_model(self) -> None:
        error: dict[str, Any] = MARS_CONTRACT["error_response"]  # type: ignore[assignment]
        model_fields = set(ErrorResponse.model_fields.keys())
        for field_name in error["required"]:
            assert (
                field_name in model_fields
            ), f"Contract error field '{field_name}' not on ErrorResponse"

    def test_error_response_optional_fields_on_model(self) -> None:
        error: dict[str, Any] = MARS_CONTRACT["error_response"]  # type: ignore[assignment]
        model_fields = set(ErrorResponse.model_fields.keys())
        for field_name in error["optional"]:
            assert (
                field_name in model_fields
            ), f"Contract optional field '{field_name}' not on ErrorResponse"

    @patch("app.routers.execute.rate_limiter")
    def test_live_error_returns_http_200(self, mock_limiter: MagicMock, client: TestClient) -> None:
        """Errors must return HTTP 200 (not 4xx) per contract guarantee."""
        mock_limiter.check_rate_limit.return_value = (
            True,
            {"limit": 100, "remaining": 99, "reset_at": 9999999999},
        )
        resp = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "nonexistent.capability",
                "org_id": "org_1",
                "user_id": "user_1",
                "turn_id": "turn_err_200",
            },
        )
        error: dict[str, Any] = MARS_CONTRACT["error_response"]  # type: ignore[assignment]
        assert resp.status_code == error["http_code"]
        data = resp.json()
        assert data["status"] == error["status_value"]


class TestMarsErrorTaxonomy:
    """All 10 error codes and 3 retry strategies must match the live enums."""

    def test_all_contract_error_codes_in_enum(self) -> None:
        """Every error code in the contract must exist in ErrorCode."""
        error_codes: dict[str, Any] = MARS_CONTRACT["error_codes"]  # type: ignore[assignment]
        enum_values = {e.value for e in ErrorCode}
        for code in error_codes:
            assert code in enum_values, f"Contract error code '{code}' not in ErrorCode enum"

    def test_all_enum_error_codes_in_contract(self) -> None:
        """Every ErrorCode enum value must be in the contract (no silent additions)."""
        error_codes: dict[str, Any] = MARS_CONTRACT["error_codes"]  # type: ignore[assignment]
        for e in ErrorCode:
            assert (
                e.value in error_codes
            ), f"ErrorCode.{e.value} exists in enum but not in MARS contract"

    def test_error_code_count(self) -> None:
        error_codes: dict[str, Any] = MARS_CONTRACT["error_codes"]  # type: ignore[assignment]
        assert len(error_codes) == 10

    def test_all_contract_retry_strategies_in_enum(self) -> None:
        """Every retry strategy in the contract must exist in RetryStrategy."""
        strategies: list[str] = MARS_CONTRACT["retry_strategies"]  # type: ignore[assignment]
        enum_values = {e.value for e in RetryStrategy}
        for s in strategies:
            assert s in enum_values, f"Contract retry strategy '{s}' not in RetryStrategy enum"

    def test_all_enum_retry_strategies_in_contract(self) -> None:
        """Every RetryStrategy enum value must be in the contract."""
        strategies: list[str] = MARS_CONTRACT["retry_strategies"]  # type: ignore[assignment]
        for e in RetryStrategy:
            assert (
                e.value in strategies
            ), f"RetryStrategy.{e.value} exists in enum but not in MARS contract"

    def test_retry_strategy_count(self) -> None:
        strategies: list[str] = MARS_CONTRACT["retry_strategies"]  # type: ignore[assignment]
        assert len(strategies) == 3

    def test_error_code_retry_mapping_matches_contract(self) -> None:
        """ERROR_RETRY_STRATEGIES must match the contract's retry mapping."""
        error_codes: dict[str, dict[str, str]] = MARS_CONTRACT["error_codes"]  # type: ignore[assignment]
        for code_str, spec in error_codes.items():
            error_code = ErrorCode(code_str)
            actual_strategy = ERROR_RETRY_STRATEGIES[error_code]
            expected_strategy = RetryStrategy(spec["retry"])
            assert actual_strategy == expected_strategy, (
                f"{code_str}: contract says retry='{spec['retry']}' "
                f"but ERROR_RETRY_STRATEGIES maps to '{actual_strategy.value}'"
            )


class TestMarsRateLimitHeaders:
    """Rate limit headers must be present on execute responses."""

    @patch("app.routers.execute.rate_limiter")
    def test_rate_limit_headers_present(self, mock_limiter: MagicMock, client: TestClient) -> None:
        mock_limiter.check_rate_limit.return_value = (
            True,
            {"limit": 100, "remaining": 99, "reset_at": 9999999999},
        )
        resp = client.post(
            "/api/v1/execute",
            json={
                "capability_key": "nonexistent.cap",
                "org_id": "org_1",
                "user_id": "user_1",
                "turn_id": "turn_rl_headers",
            },
        )
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers
