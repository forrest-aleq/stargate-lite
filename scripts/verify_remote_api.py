#!/usr/bin/env python3
"""
Remote deployment smoke checks for Stargate.

Checks:
1. /health returns HTTP 200 and status=healthy
2. /api/v1/capabilities returns at least min-capabilities
3. /api/v1/execute works with calc.npv
4. /version reports the expected build commit when --expected-sha is provided
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import requests


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify deployed Stargate instance")
    parser.add_argument("--base-url", required=True, help="Base API URL")
    parser.add_argument("--api-key", required=True, help="X-API-Key for protected endpoints")
    parser.add_argument(
        "--min-capabilities",
        type=int,
        default=1,
        help="Minimum expected capabilities count",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=20,
        help="HTTP timeout in seconds",
    )
    parser.add_argument(
        "--expected-sha",
        default=None,
        help="Expected deployed commit SHA; verifies /version build.commit_sha when set",
    )
    parser.add_argument(
        "--org-id",
        default="deploy-smoke-org",
        help="org_id for execute smoke test",
    )
    parser.add_argument(
        "--user-id",
        default="deploy-smoke-user",
        help="user_id for execute smoke test",
    )
    return parser


def _join(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _assert_health(base_url: str, timeout_seconds: int) -> dict[str, Any]:
    url = _join(base_url, "/health")
    resp = requests.get(url, timeout=timeout_seconds)
    if resp.status_code != 200:
        raise RuntimeError(f"/health returned HTTP {resp.status_code}")
    payload = resp.json()
    status = str(payload.get("status", "")).lower()
    if status != "healthy":
        raise RuntimeError(f"/health status must be 'healthy', found '{status or '<missing>'}'")
    return payload


def _assert_version(base_url: str, expected_sha: str, timeout_seconds: int) -> dict[str, Any]:
    url = _join(base_url, "/version")
    resp = requests.get(url, timeout=timeout_seconds)
    if resp.status_code != 200:
        raise RuntimeError(f"/version returned HTTP {resp.status_code}")
    payload = resp.json()
    build = payload.get("build")
    if not isinstance(build, dict):
        raise RuntimeError("/version missing build provenance")
    deployed_sha = build.get("commit_sha")
    if deployed_sha != expected_sha:
        deployed = deployed_sha[:12] if isinstance(deployed_sha, str) else "<missing>"
        raise RuntimeError(
            f"/version commit mismatch: deployed {deployed}, expected {expected_sha[:12]}"
        )
    return payload


def _extract_capability_count(payload: dict[str, Any]) -> int:
    count = payload.get("count")
    if isinstance(count, int):
        return count
    capabilities = payload.get("capabilities")
    if isinstance(capabilities, dict):
        return len(capabilities)
    if isinstance(capabilities, list):
        return len(capabilities)
    return 0


def _assert_capabilities(
    base_url: str,
    api_key: str,
    min_capabilities: int,
    timeout_seconds: int,
) -> int:
    url = _join(base_url, "/api/v1/capabilities")
    resp = requests.get(url, headers={"X-API-Key": api_key}, timeout=timeout_seconds)
    if resp.status_code != 200:
        raise RuntimeError(f"/api/v1/capabilities returned HTTP {resp.status_code}")
    payload = resp.json()
    count = _extract_capability_count(payload)
    if count < min_capabilities:
        raise RuntimeError(
            f"Capabilities count too low: found {count}, expected at least {min_capabilities}"
        )
    return count


def _assert_execute(
    base_url: str, api_key: str, timeout_seconds: int, org_id: str, user_id: str
) -> None:
    url = _join(base_url, "/api/v1/execute")
    payload = {
        "capability_key": "calc.npv",
        "org_id": org_id,
        "user_id": user_id,
        "turn_id": f"deploy-smoke-{int(time.time())}",
        "args": {
            "discount_rate": 0.10,
            "cash_flows": [-1000, 400, 400, 400],
        },
    }
    resp = requests.post(
        url,
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=timeout_seconds,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"/api/v1/execute returned HTTP {resp.status_code}")
    data = resp.json()
    if str(data.get("status", "")).lower() != "success":
        raise RuntimeError(f"/api/v1/execute did not return success status: {data}")
    outputs = data.get("outputs")
    if not isinstance(outputs, dict) or "npv" not in outputs:
        raise RuntimeError("/api/v1/execute success payload missing outputs.npv")


def main() -> int:
    args = _build_parser().parse_args()

    try:
        health = _assert_health(args.base_url, args.timeout_seconds)
        version = (
            _assert_version(args.base_url, args.expected_sha, args.timeout_seconds)
            if args.expected_sha
            else None
        )
        count = _assert_capabilities(
            args.base_url,
            args.api_key,
            args.min_capabilities,
            args.timeout_seconds,
        )
        _assert_execute(
            args.base_url,
            args.api_key,
            args.timeout_seconds,
            args.org_id,
            args.user_id,
        )
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1

    print("Verification passed")
    print(f"  health.status={health.get('status')}")
    if version:
        print(f"  version.commit={args.expected_sha[:12]}")
    print(f"  capabilities.count={count}")
    print("  execute.calc.npv=ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
