#!/usr/bin/env python3
"""
Check Railway environment readiness for deployment/promotion.

This script validates:
1. Core runtime variables are present
2. ENABLED_SERVICES is set
3. Key-gated env vars exist for every enabled service
4. Optional environment-value expectation (for example ENVIRONMENT=production)

It does not print secret values. It only reports presence/absence.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

CORE_REQUIRED_VARS = (
    "API_SECRET_KEY",
    "ENCRYPTION_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "ENABLED_SERVICES",
    "ENVIRONMENT",
)


def _is_missing(value: str | None) -> bool:
    return value is None or value.strip() == ""


def _fetch_railway_vars(environment: str, service: str, attempts: int = 3) -> dict[str, str]:
    cmd = ["railway", "variables", "--environment", environment, "--json"]
    if service:
        cmd.extend(["--service", service])

    last_error = ""
    for attempt in range(1, attempts + 1):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            last_error = result.stderr.strip() or result.stdout.strip()
        else:
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                last_error = "Railway variables output was not valid JSON"
            else:
                break

        if attempt < attempts:
            print(
                "Railway variables read failed; retrying "
                f"({attempt}/{attempts}): {last_error}",
                file=sys.stderr,
            )
            time.sleep(min(10, attempt * 2))
    else:
        raise RuntimeError(
            "Failed to read Railway variables.\n"
            f"Command: {' '.join(cmd)}\n"
            f"stderr: {last_error}"
        )

    if not isinstance(payload, dict):
        raise RuntimeError("Railway variables JSON must be an object")

    normalized: dict[str, str] = {}
    for key, value in payload.items():
        if value is None:
            normalized[key] = ""
        else:
            normalized[key] = str(value)
    return normalized


def _load_key_gate_map(registry_path: Path) -> dict[str, str]:
    text = registry_path.read_text()
    match = re.search(
        r"_KEY_GATED_SERVICES:\s*dict\[str,\s*str\]\s*=\s*\{(?P<body>.*?)\n\}",
        text,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"Unable to parse _KEY_GATED_SERVICES from {registry_path}")

    body = match.group("body")
    pairs = re.findall(r'"([a-zA-Z0-9_]+)"\s*:\s*"([A-Z0-9_]+)"', body)
    if not pairs:
        raise RuntimeError(f"No key-gated service entries found in {registry_path}")

    return dict(pairs)


def _parse_enabled_services(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _print_list(title: str, items: list[str]) -> None:
    if not items:
        print(f"{title}: none")
        return
    print(f"{title}:")
    for item in items:
        print(f"  - {item}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check Railway env readiness for Stargate")
    parser.add_argument(
        "--environment",
        required=True,
        help="Railway environment name (for example: staging, production)",
    )
    parser.add_argument(
        "--service",
        default="",
        help="Optional Railway service name (defaults to linked service)",
    )
    parser.add_argument(
        "--expect-env-value",
        default="",
        help="If provided, ENVIRONMENT must equal this value",
    )
    parser.add_argument(
        "--require-service",
        action="append",
        default=[],
        help="Service that must appear in ENABLED_SERVICES. Can be passed multiple times.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    registry_path = root / "app" / "registry" / "__init__.py"

    try:
        vars_map = _fetch_railway_vars(args.environment, args.service)
        key_gate_map = _load_key_gate_map(registry_path)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2

    enabled_raw = vars_map.get("ENABLED_SERVICES", "")
    enabled_services = _parse_enabled_services(enabled_raw)

    missing_core = [name for name in CORE_REQUIRED_VARS if _is_missing(vars_map.get(name))]

    missing_enabled_key_gates: list[str] = []
    for service in enabled_services:
        gate_env = key_gate_map.get(service)
        if gate_env and _is_missing(vars_map.get(gate_env)):
            missing_enabled_key_gates.append(f"{service}:{gate_env}")

    missing_required_services = [
        service for service in args.require_service if service not in enabled_services
    ]

    env_value_mismatch = ""
    if args.expect_env_value:
        actual = vars_map.get("ENVIRONMENT", "")
        if actual != args.expect_env_value:
            env_value_mismatch = (
                f"ENVIRONMENT expected '{args.expect_env_value}', found '{actual or '<missing>'}'"
            )

    print(
        "Readiness check target: "
        f"environment={args.environment} service={args.service or '<linked>'}"
    )
    print(f"Enabled services ({len(enabled_services)}): {', '.join(enabled_services) or '<none>'}")

    _print_list("Missing core vars", missing_core)
    _print_list("Missing key-gated vars for enabled services", missing_enabled_key_gates)
    _print_list("Required services missing from ENABLED_SERVICES", missing_required_services)

    if env_value_mismatch:
        print("Environment mismatch:")
        print(f"  - {env_value_mismatch}")

    has_errors = bool(
        missing_core or missing_enabled_key_gates or missing_required_services or env_value_mismatch
    )
    if has_errors:
        print("Result: FAILED")
        return 1

    print("Result: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
