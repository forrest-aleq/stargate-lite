from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.requests import Request

from app import auth as auth_module
from app.auth import verify_api_key


def _build_request(
    body: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> Request:
    payload = json.dumps(body or {}).encode("utf-8")
    delivered = False
    raw_headers = [(b"content-type", b"application/json")]
    for key, value in Headers(headers or {}).raw:
        raw_headers.append((key, value))

    async def receive() -> dict[str, object]:
        nonlocal delivered
        if delivered:
            return {"type": "http.request", "body": b"", "more_body": False}

        delivered = True
        return {"type": "http.request", "body": payload, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/execute",
        "headers": raw_headers,
    }
    return Request(scope, receive)


@pytest.mark.asyncio
async def test_verify_api_key_accepts_client_registry_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "API_CLIENT_KEYS_JSON",
        json.dumps(
            [
                {
                    "key_id": "sdk-client",
                    "secret": "sdk-secret",
                    "org_allowlist": ["org_allowed"],
                }
            ]
        ),
    )

    request = _build_request({"org_id": "org_allowed"})

    assert await verify_api_key(request, x_api_key="sdk-secret") is True
    assert request.state.api_client["key_id"] == "sdk-client"
    assert request.state.api_client["auth_mode"] == "client_registry"


@pytest.mark.asyncio
async def test_verify_api_key_accepts_legacy_shared_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_SECRET_KEY", "legacy-secret")
    monkeypatch.delenv("API_CLIENT_KEYS_JSON", raising=False)

    request = _build_request({"org_id": "org_allowed"})

    assert await verify_api_key(request, x_api_key="legacy-secret") is True
    assert request.state.api_client["key_id"] == "legacy-shared-key"
    assert request.state.api_client["auth_mode"] == "legacy_shared_key"


@pytest.mark.asyncio
async def test_verify_api_key_rejects_org_outside_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "API_CLIENT_KEYS_JSON",
        json.dumps(
            [
                {
                    "key_id": "restricted-client",
                    "secret": "restricted-secret",
                    "org_allowlist": ["org_allowed"],
                }
            ]
        ),
    )

    request = _build_request({"org_id": "org_blocked"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(request, x_api_key="restricted-secret")

    assert exc_info.value.status_code == 403
    assert "org_blocked" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_api_key_rejects_org_outside_allowlist_from_tenant_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "API_CLIENT_KEYS_JSON",
        json.dumps(
            [
                {
                    "key_id": "restricted-client",
                    "secret": "restricted-secret",
                    "org_allowlist": ["org_allowed"],
                }
            ]
        ),
    )

    request = _build_request(headers={"X-Tenant-ID": "org_blocked"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(request, x_api_key="restricted-secret")

    assert exc_info.value.status_code == 403
    assert "org_blocked" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_api_key_uses_client_secret_for_hmac(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "signed-secret"
    monkeypatch.setenv(
        "API_CLIENT_KEYS_JSON",
        json.dumps(
            [
                {
                    "key_id": "signed-client",
                    "secret": secret,
                }
            ]
        ),
    )

    request = _build_request({"org_id": "org_allowed", "turn_id": "turn-1"})
    timestamp = str(int(time.time()))
    body = await request.body()
    signature = hmac.new(
        secret.encode(),
        timestamp.encode() + body,
        hashlib.sha256,
    ).hexdigest()

    assert await verify_api_key(
        request,
        x_api_key=secret,
        x_timestamp=timestamp,
        x_signature_256=f"sha256={signature}",
    )


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


def _introspection_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "active": True,
        "api_key_id": "key_s1",
        "project_id": "proj_123",
        "environment_id": "env_staging",
        "client_id": "client_sdk",
        "service": "S1",
        "key_prefix": "s1_test",
        "scope_set": ["execute"],
    }
    payload.update(overrides)
    return payload


def _configure_control_plane(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_SECRET_KEY", raising=False)
    monkeypatch.delenv("API_CLIENT_KEYS_JSON", raising=False)
    monkeypatch.setenv("CONTROL_PLANE_BASE_URL", "https://baby-mars.example")
    monkeypatch.setenv("CONTROL_PLANE_API_KEY", "cp-secret")


@pytest.mark.asyncio
async def test_verify_api_key_enforces_control_plane_key_scoped_tenant_grant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_control_plane(monkeypatch)

    def fake_post(url: str, **kwargs: object) -> _FakeResponse:
        assert url == "https://baby-mars.example/cp/v1/keys/introspect"
        assert kwargs["headers"] == {"X-Control-Plane-Key": "cp-secret"}
        assert kwargs["json"] == {"secret": "s1-secret"}
        return _FakeResponse(_introspection_payload())

    def fake_get(url: str, **kwargs: object) -> _FakeResponse:
        assert url == "https://baby-mars.example/cp/v1/projects/proj_123/tenant-grants"
        assert kwargs["headers"] == {"X-Control-Plane-Key": "cp-secret"}
        return _FakeResponse(
            [
                {
                    "tenant_grant_id": "grant_key_scoped",
                    "project_id": "proj_123",
                    "environment_id": "env_staging",
                    "client_id": "client_sdk",
                    "api_key_id": "key_s1",
                    "tenant_id": "org_allowed",
                    "grant_type": "allow",
                }
            ]
        )

    monkeypatch.setattr(auth_module.requests, "post", fake_post)
    monkeypatch.setattr(auth_module.requests, "get", fake_get)

    request = _build_request({"org_id": "org_allowed", "turn_id": "turn-1"})

    assert await verify_api_key(request, x_api_key="s1-secret") is True
    assert request.state.api_client["auth_mode"] == "control_plane"
    assert request.state.api_client["project_id"] == "proj_123"
    assert request.state.api_client["client_id"] == "client_sdk"


@pytest.mark.asyncio
async def test_verify_api_key_enforces_control_plane_tenant_grant_from_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_control_plane(monkeypatch)
    monkeypatch.setattr(
        auth_module.requests,
        "post",
        lambda *_args, **_kwargs: _FakeResponse(_introspection_payload()),
    )
    monkeypatch.setattr(
        auth_module.requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(
            [
                {
                    "tenant_grant_id": "grant_key_scoped",
                    "project_id": "proj_123",
                    "environment_id": "env_staging",
                    "client_id": "client_sdk",
                    "api_key_id": "key_s1",
                    "tenant_id": "org_allowed",
                    "grant_type": "allow",
                }
            ]
        ),
    )

    request = _build_request(headers={"X-Tenant-ID": "org_allowed"})

    assert await verify_api_key(request, x_api_key="s1-secret") is True


@pytest.mark.asyncio
async def test_verify_api_key_rejects_control_plane_key_without_tenant_grant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_control_plane(monkeypatch)
    monkeypatch.setattr(
        auth_module.requests,
        "post",
        lambda *_args, **_kwargs: _FakeResponse(_introspection_payload()),
    )
    monkeypatch.setattr(
        auth_module.requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse([]),
    )

    request = _build_request({"org_id": "org_denied", "turn_id": "turn-1"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(request, x_api_key="s1-secret")

    assert exc_info.value.status_code == 403
    assert "org_denied" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_api_key_rejects_broad_control_plane_allow_grant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_control_plane(monkeypatch)
    monkeypatch.setattr(
        auth_module.requests,
        "post",
        lambda *_args, **_kwargs: _FakeResponse(_introspection_payload()),
    )
    monkeypatch.setattr(
        auth_module.requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(
            [
                {
                    "tenant_grant_id": "grant_broad_allow",
                    "project_id": "proj_123",
                    "environment_id": "env_staging",
                    "client_id": "client_sdk",
                    "api_key_id": None,
                    "tenant_id": "org_allowed",
                    "grant_type": "allow",
                }
            ]
        ),
    )

    request = _build_request({"org_id": "org_allowed", "turn_id": "turn-1"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(request, x_api_key="s1-secret")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_verify_api_key_control_plane_deny_grant_wins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_control_plane(monkeypatch)
    monkeypatch.setattr(
        auth_module.requests,
        "post",
        lambda *_args, **_kwargs: _FakeResponse(_introspection_payload()),
    )
    monkeypatch.setattr(
        auth_module.requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(
            [
                {
                    "tenant_grant_id": "grant_allow",
                    "project_id": "proj_123",
                    "environment_id": "env_staging",
                    "client_id": "client_sdk",
                    "api_key_id": "key_s1",
                    "tenant_id": "org_blocked",
                    "grant_type": "allow",
                },
                {
                    "tenant_grant_id": "grant_deny",
                    "project_id": "proj_123",
                    "environment_id": "env_staging",
                    "client_id": "client_sdk",
                    "api_key_id": "key_s1",
                    "tenant_id": "org_blocked",
                    "grant_type": "deny",
                },
            ]
        ),
    )

    request = _build_request({"org_id": "org_blocked", "turn_id": "turn-1"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(request, x_api_key="s1-secret")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_verify_api_key_rejects_non_s1_control_plane_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_control_plane(monkeypatch)
    monkeypatch.setattr(
        auth_module.requests,
        "post",
        lambda *_args, **_kwargs: _FakeResponse(_introspection_payload(service="M1")),
    )
    monkeypatch.setattr(
        auth_module.requests,
        "get",
        lambda *_args, **_kwargs: pytest.fail("tenant grants should not be fetched"),
    )

    request = _build_request({"org_id": "org_allowed", "turn_id": "turn-1"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(request, x_api_key="m1-secret")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Invalid API Key"
