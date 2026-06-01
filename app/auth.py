"""
Authentication utilities for Stargate Lite.

Validates API key and optional HMAC-SHA256 request signatures.
Baby MARS sends X-API-Key, X-Timestamp, and X-Signature-256 on every request.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from asyncio import to_thread
from dataclasses import dataclass

import requests
from fastapi import Header, HTTPException, Request

API_CLIENT_KEYS_JSON = "API_CLIENT_KEYS_JSON"
CONTROL_PLANE_BASE_URL = "CONTROL_PLANE_BASE_URL"
CONTROL_PLANE_API_KEY = "CONTROL_PLANE_API_KEY"

# Reject requests with timestamps older than 5 minutes (replay protection)
SIGNATURE_TOLERANCE_SECONDS = 300


@dataclass(frozen=True)
class ApiClientPrincipal:
    key_id: str
    secret: str
    org_allowlist: tuple[str, ...] = ()
    auth_mode: str = "client_registry"
    project_id: str | None = None
    environment_id: str | None = None
    client_id: str | None = None
    service: str | None = None


def _get_legacy_api_secret() -> str:
    return os.getenv("API_SECRET_KEY", "").strip()


def _load_client_principals() -> list[ApiClientPrincipal]:
    raw = os.getenv(API_CLIENT_KEYS_JSON, "").strip()

    if not raw:
        return []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"{API_CLIENT_KEYS_JSON} is not valid JSON",
        ) from exc

    if not isinstance(payload, list):
        raise HTTPException(
            status_code=500,
            detail=f"{API_CLIENT_KEYS_JSON} must be a JSON array",
        )

    principals: list[ApiClientPrincipal] = []

    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=500,
                detail=f"{API_CLIENT_KEYS_JSON}[{index}] must be an object",
            )

        secret = item.get("secret")
        key_id = item.get("key_id")
        org_allowlist = item.get("org_allowlist", [])

        if not isinstance(secret, str) or not secret.strip():
            raise HTTPException(
                status_code=500,
                detail=f"{API_CLIENT_KEYS_JSON}[{index}].secret must be a non-empty string",
            )

        if key_id is None:
            key_id = f"client-{index + 1}"

        if not isinstance(key_id, str) or not key_id.strip():
            raise HTTPException(
                status_code=500,
                detail=f"{API_CLIENT_KEYS_JSON}[{index}].key_id must be a string",
            )

        if not isinstance(org_allowlist, list) or any(
            not isinstance(org_id, str) or not org_id.strip() for org_id in org_allowlist
        ):
            raise HTTPException(
                status_code=500,
                detail=(
                    f"{API_CLIENT_KEYS_JSON}[{index}].org_allowlist must be an array of strings"
                ),
            )

        principals.append(
            ApiClientPrincipal(
                key_id=key_id,
                secret=secret,
                org_allowlist=tuple(org_allowlist),
            )
        )

    return principals


def _resolve_api_client(x_api_key: str | None) -> ApiClientPrincipal | None:
    if not x_api_key:
        return None

    legacy_secret = _get_legacy_api_secret()

    if legacy_secret and secrets.compare_digest(x_api_key, legacy_secret):
        return ApiClientPrincipal(
            key_id="legacy-shared-key",
            secret=legacy_secret,
            auth_mode="legacy_shared_key",
        )

    for principal in _load_client_principals():
        if secrets.compare_digest(x_api_key, principal.secret):
            return principal

    return None


def _get_control_plane_base_url() -> str:
    return os.getenv(CONTROL_PLANE_BASE_URL, "").strip().rstrip("/")


def _get_control_plane_api_key() -> str:
    return os.getenv(CONTROL_PLANE_API_KEY, "").strip()


def _control_plane_auth_configured() -> bool:
    return bool(_get_control_plane_base_url() and _get_control_plane_api_key())


def _as_non_empty_string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _get_control_plane_json(method: str, path: str, *, body: dict[str, object]) -> object:
    base_url = _get_control_plane_base_url()
    control_plane_key = _get_control_plane_api_key()
    if not base_url or not control_plane_key:
        return None

    try:
        if method == "POST":
            response = requests.post(
                f"{base_url}{path}",
                headers={"X-Control-Plane-Key": control_plane_key},
                json=body,
                timeout=5,
            )
        else:
            response = requests.get(
                f"{base_url}{path}",
                headers={"X-Control-Plane-Key": control_plane_key},
                timeout=5,
            )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="Control plane API-key authorization unavailable",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail="Control plane API-key authorization returned invalid JSON",
        ) from exc


def _introspect_control_plane_api_key(x_api_key: str) -> ApiClientPrincipal | None:
    payload = _get_control_plane_json(
        "POST",
        "/cp/v1/keys/introspect",
        body={"secret": x_api_key},
    )

    if not isinstance(payload, dict) or not payload.get("active"):
        return None

    if payload.get("service") != "S1":
        return None

    key_id = payload.get("api_key_id") or payload.get("key_prefix") or "control-plane-key"
    if not isinstance(key_id, str) or not key_id.strip():
        key_id = "control-plane-key"

    return ApiClientPrincipal(
        key_id=key_id,
        secret=x_api_key,
        auth_mode="control_plane",
        project_id=_as_non_empty_string(payload.get("project_id")),
        environment_id=_as_non_empty_string(payload.get("environment_id")),
        client_id=_as_non_empty_string(payload.get("client_id")),
        service=_as_non_empty_string(payload.get("service")),
    )


async def _resolve_control_plane_api_client(
    x_api_key: str | None,
) -> ApiClientPrincipal | None:
    if not x_api_key:
        return None
    return await to_thread(_introspect_control_plane_api_key, x_api_key)


async def _extract_org_id(request: Request) -> str | None:
    body = await request.body()

    if not body:
        return None

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    org_id = payload.get("org_id")
    if isinstance(org_id, str) and org_id.strip():
        return org_id

    return None


def _grant_applies(
    grant: dict[str, object],
    principal: ApiClientPrincipal,
) -> bool:
    return (
        _as_non_empty_string(grant.get("environment_id")) in (None, principal.environment_id)
        and _as_non_empty_string(grant.get("client_id")) in (None, principal.client_id)
        and _as_non_empty_string(grant.get("api_key_id")) in (None, principal.key_id)
    )


def _control_plane_key_has_tenant_access(
    principal: ApiClientPrincipal,
    tenant_id: str,
) -> bool:
    if principal.auth_mode != "control_plane":
        return True
    if principal.project_id is None:
        return False

    payload = _get_control_plane_json(
        "GET",
        f"/cp/v1/projects/{principal.project_id}/tenant-grants",
        body={},
    )
    if not isinstance(payload, list):
        raise HTTPException(
            status_code=503,
            detail="Control plane tenant grants returned invalid JSON",
        )

    applicable = [
        grant for grant in payload if isinstance(grant, dict) and _grant_applies(grant, principal)
    ]
    for grant in applicable:
        if grant.get("grant_type") == "deny" and grant.get("tenant_id") == tenant_id:
            return False

    return any(
        grant.get("grant_type") == "allow" and grant.get("tenant_id") == tenant_id
        for grant in applicable
    )


async def _enforce_control_plane_tenant_grant(
    request: Request,
    principal: ApiClientPrincipal,
) -> None:
    if principal.auth_mode != "control_plane":
        return

    org_id = await _extract_org_id(request)
    if org_id is None:
        return

    allowed = await to_thread(_control_plane_key_has_tenant_access, principal, org_id)
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"API key '{principal.key_id}' is not allowed for org_id '{org_id}'",
        )


async def verify_api_key(
    request: Request,
    x_api_key: str | None = Header(None),
    x_timestamp: str | None = Header(None, alias="X-Timestamp"),
    x_signature_256: str | None = Header(None, alias="X-Signature-256"),
) -> bool:
    """Verify API key and optional HMAC-SHA256 request signature.

    When X-Timestamp and X-Signature-256 headers are present, validates:
    1. Timestamp is within 5 minutes of server time (replay protection)
    2. HMAC-SHA256(timestamp + body) matches the signature (tamper protection)

    Baby MARS sends: X-Signature-256: sha256={hex}
    Signing format:  HMAC-SHA256(key=API_SECRET_KEY, msg=timestamp + body)
    """
    x_api_key = x_api_key if isinstance(x_api_key, str) else None
    x_timestamp = x_timestamp if isinstance(x_timestamp, str) else None
    x_signature_256 = x_signature_256 if isinstance(x_signature_256, str) else None
    principal = _resolve_api_client(x_api_key)
    if principal is None:
        principal = await _resolve_control_plane_api_client(x_api_key)

    if (
        not _get_legacy_api_secret()
        and not _load_client_principals()
        and not _control_plane_auth_configured()
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "No Stargate API credentials are configured. Set API_SECRET_KEY or "
                "API_CLIENT_KEYS_JSON, or configure control-plane auth."
            ),
        )

    if principal is None:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    if principal.org_allowlist:
        org_id = await _extract_org_id(request)
        if org_id is not None and org_id not in principal.org_allowlist:
            raise HTTPException(
                status_code=403,
                detail=f"API key '{principal.key_id}' is not allowed for org_id '{org_id}'",
            )

    await _enforce_control_plane_tenant_grant(request, principal)

    request.state.api_client = {
        "key_id": principal.key_id,
        "auth_mode": principal.auth_mode,
        "org_allowlist": list(principal.org_allowlist),
        "project_id": principal.project_id,
        "environment_id": principal.environment_id,
        "client_id": principal.client_id,
        "service": principal.service,
    }

    # Validate HMAC signature when both headers are present
    if x_timestamp is not None and x_signature_256 is not None:
        try:
            ts = int(x_timestamp)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid X-Timestamp header") from exc

        if abs(int(time.time()) - ts) > SIGNATURE_TOLERANCE_SECONDS:
            raise HTTPException(status_code=403, detail="Request timestamp expired")

        body = await request.body()
        # Baby MARS signs: HMAC-SHA256(key, timestamp + body)
        message = x_timestamp.encode() + body
        expected = hmac.new(principal.secret.encode(), message, hashlib.sha256).hexdigest()

        # Baby MARS sends "sha256={hex}" — strip the prefix
        signature = x_signature_256.removeprefix("sha256=")
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="Invalid request signature")

    return True
