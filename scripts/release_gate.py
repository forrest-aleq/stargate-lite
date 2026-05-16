#!/usr/bin/env python3
"""Release provenance gate for staging-to-main promotion.

This script enforces the source-control rule that production releases come from
code already exercised on staging. It is intentionally independent of GitHub so
it can run locally, in CI, or from a release workflow.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


class ReleaseGateError(Exception):
    """Raised when a release provenance rule fails."""


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        raise ReleaseGateError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def _fetch_refs(remote: str, main_branch: str, staging_branch: str) -> None:
    _run_git(["fetch", remote, main_branch, staging_branch, "--prune"])


def _resolve(ref: str) -> str:
    return _run_git(["rev-parse", "--verify", ref])


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _short(sha: str) -> str:
    return sha[:12]


def _load_stack_lock(path: Path, service: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ReleaseGateError(f"stack lock not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseGateError(f"stack lock is invalid JSON: {path}") from exc

    services = payload.get("services")
    if not isinstance(services, dict) or service not in services:
        raise ReleaseGateError(f"stack lock does not contain service '{service}'")

    entry = services[service]
    if not isinstance(entry, dict):
        raise ReleaseGateError(f"stack lock service '{service}' must be an object")
    return entry


def _require_stack_lock_match(path: Path, service: str, target_sha: str) -> dict[str, Any]:
    entry = _load_stack_lock(path, service)
    locked_sha = entry.get("release_sha") or entry.get("sha")
    if not isinstance(locked_sha, str) or not locked_sha:
        raise ReleaseGateError(f"stack lock service '{service}' is missing release_sha")
    if target_sha != locked_sha:
        raise ReleaseGateError(
            f"target {_short(target_sha)} does not match locked {service} "
            f"sha {_short(locked_sha)}"
        )
    return entry


def _write_proof(path: Path, proof: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("promotion", "production"),
        default="promotion",
        help="promotion gates staging-to-main PRs; production gates deploy targets",
    )
    parser.add_argument("--service", default="stargate-lite")
    parser.add_argument("--target-ref", default="HEAD")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--main-branch", default="main")
    parser.add_argument("--staging-branch", default="staging")
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--stack-lock", type=Path)
    parser.add_argument("--write-proof", type=Path)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    main_ref = f"{args.remote}/{args.main_branch}"
    staging_ref = f"{args.remote}/{args.staging_branch}"
    checks: list[dict[str, Any]] = []

    try:
        if not args.skip_fetch:
            _fetch_refs(args.remote, args.main_branch, args.staging_branch)

        target_sha = _resolve(args.target_ref)
        main_sha = _resolve(main_ref)
        staging_sha = _resolve(staging_ref)

        main_is_in_staging = _is_ancestor(main_sha, staging_sha)
        checks.append(
            {
                "name": "main_is_ancestor_of_staging",
                "passed": main_is_in_staging,
                "details": f"{_short(main_sha)} <= {_short(staging_sha)}",
            }
        )
        if not main_is_in_staging:
            raise ReleaseGateError(
                f"{main_ref} ({_short(main_sha)}) is not an ancestor of "
                f"{staging_ref} ({_short(staging_sha)})"
            )

        target_is_in_staging = _is_ancestor(target_sha, staging_sha)
        checks.append(
            {
                "name": "target_is_contained_in_staging",
                "passed": target_is_in_staging,
                "details": f"{_short(target_sha)} <= {_short(staging_sha)}",
            }
        )
        if not target_is_in_staging:
            raise ReleaseGateError(
                f"target {args.target_ref} ({_short(target_sha)}) is not contained in "
                f"{staging_ref} ({_short(staging_sha)})"
            )

        if args.mode == "production":
            target_is_in_main = _is_ancestor(target_sha, main_sha)
            checks.append(
                {
                    "name": "target_is_contained_in_main",
                    "passed": target_is_in_main,
                    "details": f"{_short(target_sha)} <= {_short(main_sha)}",
                }
            )
            if not target_is_in_main:
                raise ReleaseGateError(
                    f"production target {args.target_ref} ({_short(target_sha)}) is not "
                    f"contained in {main_ref} ({_short(main_sha)})"
                )

        stack_entry: dict[str, Any] | None = None
        if args.stack_lock:
            stack_entry = _require_stack_lock_match(args.stack_lock, args.service, target_sha)
            checks.append(
                {
                    "name": "target_matches_stack_lock",
                    "passed": True,
                    "details": _short(target_sha),
                }
            )

        proof = {
            "service": args.service,
            "mode": args.mode,
            "target_ref": args.target_ref,
            "target_sha": target_sha,
            "main_ref": main_ref,
            "main_sha": main_sha,
            "staging_ref": staging_ref,
            "staging_sha": staging_sha,
            "stack_lock": str(args.stack_lock) if args.stack_lock else None,
            "stack_entry": stack_entry,
            "checks": checks,
        }

        if args.write_proof:
            _write_proof(args.write_proof, proof)

        print(json.dumps(proof, indent=2, sort_keys=True))
        return 0
    except ReleaseGateError as exc:
        print(f"RELEASE GATE FAILED: {exc}", file=sys.stderr)
        if checks:
            print(json.dumps({"checks": checks}, indent=2, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
