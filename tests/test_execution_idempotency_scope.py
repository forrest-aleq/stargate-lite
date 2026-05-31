from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import app, verify_api_key
from app.redis_client import (
    build_execution_idempotency_key,
    build_execution_lock_key,
    redis_client,
)
from app.routers import execute as execute_router


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def ping(self) -> bool:
        return True

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, name: str, time: int, value: str) -> bool:
        self.store[name] = value
        return True

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool:
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    def delete(self, key: str) -> int:
        existed = key in self.store
        self.store.pop(key, None)
        return int(existed)


def test_execution_idempotency_keys_are_org_scoped() -> None:
    assert build_execution_idempotency_key("org_a", "turn_1", "vendor.create") != (
        build_execution_idempotency_key("org_b", "turn_1", "vendor.create")
    )
    assert build_execution_lock_key("org_a", "turn_1", "vendor.create") != (
        build_execution_lock_key("org_b", "turn_1", "vendor.create")
    )


def test_execution_cache_does_not_cross_orgs(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeRedis()
    monkeypatch.setattr(redis_client, "_redis_client", fake)

    response = {"status": "success", "outputs": {"vendor_id": "org_a_vendor"}}
    assert redis_client.cache_execution_response("org_a", "turn_1", "vendor.create", response)

    assert redis_client.get_cached_execution_response("org_b", "turn_1", "vendor.create") is None
    assert (
        redis_client.get_cached_execution_response("org_a", "turn_1", "vendor.create") == response
    )


def test_execution_locks_are_org_scoped(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeRedis()
    monkeypatch.setattr(redis_client, "_redis_client", fake)

    assert redis_client.acquire_execution_lock("org_a", "turn_1", "vendor.create")
    assert not redis_client.acquire_execution_lock("org_a", "turn_1", "vendor.create")
    assert redis_client.acquire_execution_lock("org_b", "turn_1", "vendor.create")


def _client() -> TestClient:
    app.dependency_overrides[verify_api_key] = lambda: True
    return TestClient(app)


def _execute_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "capability_key": "vendor.create",
        "org_id": "org_test",
        "user_id": "user_test",
        "turn_id": "turn_test",
        "args": {},
    }
    payload.update(overrides)
    return payload


def test_execute_fails_closed_when_idempotency_store_is_unavailable(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(execute_router, "is_idempotency_available", lambda: False)
    monkeypatch.setattr(execute_router, "get_capability", MagicMock())

    response = _client().post("/api/v1/execute", json=_execute_payload())

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "error"
    assert data["details"]["reason"] == "idempotency_unavailable"
    execute_router.get_capability.assert_not_called()


def test_execute_rejects_concurrent_duplicate_without_running_handler(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(execute_router, "is_idempotency_available", lambda: True)
    monkeypatch.setattr(
        execute_router,
        "check_idempotency_cache",
        AsyncMock(side_effect=[None, None]),
    )
    monkeypatch.setattr(execute_router, "acquire_idempotency_lock", AsyncMock(return_value=False))
    monkeypatch.setattr(execute_router, "get_capability", MagicMock())

    response = _client().post("/api/v1/execute", json=_execute_payload())

    assert response.status_code == 409
    assert response.headers["Retry-After"] == "1"
    data = response.json()
    assert data["status"] == "error"
    assert data["details"]["reason"] == "execution_in_progress"
    execute_router.get_capability.assert_not_called()
