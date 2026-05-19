#!/usr/bin/env python3
"""Verify Stargate Lite release infrastructure without printing secret values."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

REQUIRED_STATUS_CHECKS = {
    "Lint & Type Check",
    "Tests",
    "Security Scan",
    "Build Check",
}

REQUIRED_GITHUB = {
    "staging": {
        "secrets": {
            "RAILWAY_TOKEN_STAGING",
            "STAGING_API_KEY",
        },
        "variables": {
            "RAILWAY_SERVICE_NAME",
            "RAILWAY_STAGING_ENVIRONMENT",
            "STAGING_MIN_CAPABILITIES",
            "STAGING_URL",
        },
    },
    "production": {
        "secrets": {
            "PRODUCTION_API_KEY",
            "RAILWAY_TOKEN_PRODUCTION",
        },
        "variables": {
            "PRODUCTION_URL",
            "RAILWAY_PRODUCTION_ENVIRONMENT",
            "RAILWAY_SERVICE_NAME",
        },
    },
}

REQUIRED_RAILWAY_CORE = {
    "API_SECRET_KEY",
    "DATABASE_URL",
    "ENABLED_SERVICES",
    "ENCRYPTION_KEY",
    "ENVIRONMENT",
    "REDIS_URL",
}

PROTECTED_BRANCHES = {"main", "staging"}


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    details: dict[str, Any]


class InfraError(Exception):
    """Raised when an infra command cannot be completed."""


def _run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        raise InfraError(f"{' '.join(args)} failed: {message}")
    return result.stdout


def _parse_names_table(output: str) -> set[str]:
    names: set[str] = set()
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        names.add(stripped.split()[0])
    return names


def _missing(required: set[str], present: set[str]) -> list[str]:
    return sorted(required - present)


def _is_missing(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _result(name: str, missing: list[str], present_count: int) -> CheckResult:
    return CheckResult(
        name=name,
        status="pass" if not missing else "fail",
        details={
            "missing": missing,
            "present_count": present_count,
        },
    )


def _github_secret_names(environment: str) -> set[str]:
    return _parse_names_table(_run(["gh", "secret", "list", "--env", environment]))


def _github_variable_names(environment: str) -> set[str]:
    return _parse_names_table(_run(["gh", "variable", "list", "--env", environment]))


def _github_environment_protection(repo: str, environment: str) -> CheckResult:
    payload = json.loads(_run(["gh", "api", f"repos/{repo}/environments/{environment}"]))
    policy = payload.get("deployment_branch_policy") or {}
    protection_rules = payload.get("protection_rules") or []
    missing: list[str] = []
    if payload.get("can_admins_bypass") is not False:
        missing.append("admins_cannot_bypass")
    if not policy.get("protected_branches"):
        missing.append("protected_branch_deployments")
    if policy.get("custom_branch_policies"):
        missing.append("custom_branch_policies_disabled")
    if not any(rule.get("type") == "branch_policy" for rule in protection_rules):
        missing.append("branch_policy_rule")
    return CheckResult(
        name=f"github.env.{environment}.protection",
        status="pass" if not missing else "fail",
        details={
            "missing": missing,
            "can_admins_bypass": payload.get("can_admins_bypass"),
            "deployment_branch_policy": policy,
        },
    )


def _railway_variables(service: str, environment: str) -> dict[str, Any]:
    raw = _run(
        [
            "railway",
            "variables",
            "--environment",
            environment,
            "--service",
            service,
            "--json",
        ]
    )
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise InfraError("railway variables returned non-object JSON")
    return payload


def _branch_protection(repo: str, branch: str) -> CheckResult:
    payload = json.loads(_run(["gh", "api", f"repos/{repo}/branches/{branch}/protection"]))
    checks = payload.get("required_status_checks") or {}
    contexts = set(checks.get("contexts") or [])
    reviews = payload.get("required_pull_request_reviews") or {}

    missing: list[str] = []
    if not payload.get("enforce_admins", {}).get("enabled"):
        missing.append("enforce_admins")
    if not reviews:
        missing.append("required_pull_request_reviews")
    elif int(reviews.get("required_approving_review_count") or 0) < 1:
        missing.append("required_approving_review_count>=1")
    if not reviews.get("dismiss_stale_reviews"):
        missing.append("dismiss_stale_reviews")
    if not REQUIRED_STATUS_CHECKS.issubset(contexts):
        missing.append("required_status_checks")
    if not payload.get("required_linear_history", {}).get("enabled"):
        missing.append("required_linear_history")
    if payload.get("allow_force_pushes", {}).get("enabled"):
        missing.append("force_pushes_disabled")
    if payload.get("allow_deletions", {}).get("enabled"):
        missing.append("deletions_disabled")
    if not payload.get("required_conversation_resolution", {}).get("enabled"):
        missing.append("required_conversation_resolution")

    return CheckResult(
        name=f"github.branch.{branch}.protection",
        status="pass" if not missing else "fail",
        details={
            "missing": missing,
            "pull_request_reviews": bool(reviews),
            "required_status_checks": sorted(contexts),
        },
    )


def _github_checks(repo: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    for environment, requirements in REQUIRED_GITHUB.items():
        secrets = _github_secret_names(environment)
        variables = _github_variable_names(environment)
        results.append(
            _result(
                f"github.env.{environment}.secrets",
                _missing(requirements["secrets"], secrets),
                len(secrets),
            )
        )
        results.append(
            _result(
                f"github.env.{environment}.variables",
                _missing(requirements["variables"], variables),
                len(variables),
            )
        )
        results.append(_github_environment_protection(repo, environment))
    for branch in sorted(PROTECTED_BRANCHES):
        results.append(_branch_protection(repo, branch))
    return results


def _railway_env_check(service: str, environment: str) -> CheckResult:
    variables = _railway_variables(service, environment)
    missing_core = sorted(
        name for name in REQUIRED_RAILWAY_CORE if _is_missing(variables.get(name))
    )
    mismatches: list[str] = []
    actual_environment = variables.get("ENVIRONMENT")
    if not _is_missing(actual_environment) and str(actual_environment) != environment:
        mismatches.append(f"ENVIRONMENT={actual_environment!s}")
    missing = [*missing_core, *mismatches]
    return CheckResult(
        name=f"railway.{service}.{environment}.variables",
        status="pass" if not missing else "fail",
        details={
            "missing": missing,
            "present_count": len(variables),
        },
    )


def _railway_checks(staging_service: str, production_service: str) -> list[CheckResult]:
    return [
        _railway_env_check(staging_service, "staging"),
        _railway_env_check(production_service, "production"),
    ]


def _repo(explicit: str | None) -> str:
    if explicit:
        return explicit
    return _run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]).strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=None, help="GitHub repo, e.g. owner/name")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    parser.add_argument("--staging-railway-service", default="stargate-lite")
    parser.add_argument("--production-railway-service", default="Stargate Lite")
    return parser.parse_args()


def _payload(
    repo: str,
    checks: list[CheckResult],
    staging_service: str,
    production_service: str,
) -> dict[str, Any]:
    failed = [check for check in checks if check.status != "pass"]
    return {
        "checks": [{"name": c.name, "status": c.status, "details": c.details} for c in checks],
        "railway_services": {
            "production": production_service,
            "staging": staging_service,
        },
        "repo": repo,
        "status": "fail" if failed else "pass",
    }


def main() -> int:
    args = _parse_args()
    try:
        repo = _repo(args.repo)
        checks = [
            *_github_checks(repo),
            *_railway_checks(args.staging_railway_service, args.production_railway_service),
        ]
    except (InfraError, json.JSONDecodeError) as exc:
        print(f"RELEASE INFRA CHECK FAILED: {exc}", file=sys.stderr)
        return 1

    payload = _payload(
        repo,
        checks,
        args.staging_railway_service,
        args.production_railway_service,
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for check in checks:
            prefix = "PASS" if check.status == "pass" else "FAIL"
            print(f"{prefix} {check.name}")
            missing = check.details.get("missing") or []
            if missing:
                print(f"  missing: {', '.join(missing)}")
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
