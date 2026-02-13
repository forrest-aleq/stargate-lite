"""
Tests for Redis-backed circuit breaker.
"""

import os

os.environ.setdefault("FILTER_THIRD_PARTY_LIB", "false")
os.environ.setdefault("DD_TRACE_ENABLED", "false")
os.environ.setdefault("DD_PATCH_MODULES", "none")

import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app import circuit_breaker
from app.circuit_breaker import (
    FAILURE_THRESHOLD,
    RECOVERY_TIMEOUT,
    is_open,
    record_failure,
    record_success,
)


@pytest.fixture(autouse=True)
def _reset_redis_mock() -> Any:
    """Provide a fresh mock Redis for each test."""
    store: dict[str, dict[str, str]] = {}

    mock_client = MagicMock()

    def _hgetall(key: str) -> dict[str, str]:
        return dict(store.get(key, {}))

    def _hset(
        key: str,
        field: str | None = None,
        value: str | None = None,
        mapping: dict[str, str] | None = None,
    ) -> int:
        if key not in store:
            store[key] = {}
        if mapping:
            store[key].update(mapping)
        elif field is not None and value is not None:
            store[key][field] = str(value)
        return 1

    def _hincrby(key: str, field: str, amount: int = 1) -> int:
        if key not in store:
            store[key] = {}
        current = int(store[key].get(field, "0"))
        new_val = current + amount
        store[key][field] = str(new_val)
        return new_val

    def _delete(key: str) -> int:
        store.pop(key, None)
        return 1

    def _expire(key: str, seconds: int) -> bool:
        return True

    def _pipeline() -> Any:
        commands: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

        class PipeMock:
            def hincrby(self, key: str, field: str, amount: int = 1) -> "PipeMock":
                commands.append(("hincrby", (key, field, amount), {}))
                return self

            def hset(
                self,
                key: str,
                field: str | None = None,
                value: str | None = None,
                mapping: dict[str, str] | None = None,
            ) -> "PipeMock":
                commands.append(
                    (
                        "hset",
                        (key,),
                        {"field": field, "value": value, "mapping": mapping},
                    )
                )
                return self

            def execute(self) -> list[Any]:
                results: list[Any] = []
                for cmd, args, kwargs in commands:
                    if cmd == "hincrby":
                        results.append(_hincrby(*args))
                    elif cmd == "hset":
                        results.append(_hset(args[0], **kwargs))
                return results

        return PipeMock()

    mock_client.hgetall = _hgetall
    mock_client.hset = _hset
    mock_client.hincrby = _hincrby
    mock_client.delete = _delete
    mock_client.expire = _expire
    mock_client.pipeline = _pipeline

    with patch.object(circuit_breaker.redis_client, "_redis_client", mock_client):
        yield store


class TestCircuitBreaker:
    """Tests for circuit breaker state machine."""

    def test_closed_circuit_allows_requests(self) -> None:
        """A fresh circuit (no failures) should allow requests."""
        assert is_open("test_service") is False

    def test_open_circuit_blocks_requests(self) -> None:
        """After threshold failures, circuit should block."""
        for _ in range(FAILURE_THRESHOLD):
            record_failure("test_service")
        assert is_open("test_service") is True

    def test_opens_after_threshold_failures(self) -> None:
        """Circuit should stay closed below threshold, open at threshold."""
        for i in range(FAILURE_THRESHOLD - 1):
            record_failure("test_service")
            assert is_open("test_service") is False, f"Should be closed at {i + 1} failures"

        record_failure("test_service")
        assert is_open("test_service") is True

    def test_transitions_to_half_open_after_recovery(self) -> None:
        """After recovery timeout, circuit should transition to half-open."""
        for _ in range(FAILURE_THRESHOLD):
            record_failure("test_service")
        assert is_open("test_service") is True

        # Simulate recovery timeout passing by backdating opened_at
        key = "stargate:circuit:test_service"
        client = circuit_breaker.redis_client._redis_client
        client.hset(key, "opened_at", str(time.time() - RECOVERY_TIMEOUT - 1))

        # Should allow the probe (half-open)
        assert is_open("test_service") is False

    def test_success_resets_half_open_to_closed(self) -> None:
        """Success during half-open should close the circuit."""
        for _ in range(FAILURE_THRESHOLD):
            record_failure("test_service")

        # Backdate to trigger half-open
        key = "stargate:circuit:test_service"
        client = circuit_breaker.redis_client._redis_client
        client.hset(key, "opened_at", str(time.time() - RECOVERY_TIMEOUT - 1))
        is_open("test_service")  # triggers half-open transition

        # Now record success
        record_success("test_service")

        # Circuit should be fully closed (key deleted)
        assert is_open("test_service") is False

    def test_no_redis_fails_open(self) -> None:
        """When Redis is unavailable, circuit should allow all requests."""
        with patch.object(circuit_breaker.redis_client, "_redis_client", None):
            assert is_open("test_service") is False
            # These should not raise
            record_failure("test_service")
            record_success("test_service")
