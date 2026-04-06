from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.auth import verify_api_key


def _build_request(body: dict[str, object] | None = None) -> Request:
    payload = json.dumps(body or {}).encode("utf-8")
    delivered = False

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
        "headers": [(b"content-type", b"application/json")],
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
