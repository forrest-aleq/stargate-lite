#!/usr/bin/env python3
"""Verify Stargate Lite release infrastructure without printing secret values."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

REQUIRED_STATUS_CHECKS = {
    "Lint & Type Check",
    "Tests",
    "Security Scan",
    "Build Check",
}
REQUIRED_APPROVING_REVIEW_COUNT = 0

REQUIRED_GITHUB = {
    "staging": {
        "secrets": {
            "STAGING_API_KEY",
        },
        "variables": {
            "ENABLE_CLOUD_RUN_DEPLOY",
            "GCP_ARTIFACT_REGISTRY_LOCATION",
            "GCP_ARTIFACT_REGISTRY_REPOSITORY",
            "GCP_CLOUD_RUN_SECRETS",
            "GCP_CLOUD_RUN_SERVICE",
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_SERVICE_ACCOUNT",
            "GCP_WORKLOAD_IDENTITY_PROVIDER",
            "STAGING_MIN_CAPABILITIES",
            "STAGING_URL",
        },
        "forbidden_secrets": {
            "RAILWAY_TOKEN",
            "RAILWAY_TOKEN_STAGING",
        },
        "forbidden_variables": {
            "RAILWAY_SERVICE_NAME",
            "RAILWAY_STAGING_ENVIRONMENT",
        },
        "forbidden_railway_url_variables": {
            "STAGING_URL",
        },
    },
    "production": {
        "secrets": {
            "PRODUCTION_API_KEY",
        },
        "variables": {
            "ENABLE_CLOUD_RUN_DEPLOY",
            "GCP_ARTIFACT_REGISTRY_LOCATION",
            "GCP_ARTIFACT_REGISTRY_REPOSITORY",
            "GCP_CLOUD_RUN_SECRETS",
            "GCP_CLOUD_RUN_SERVICE",
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_SERVICE_ACCOUNT",
            "GCP_WORKLOAD_IDENTITY_PROVIDER",
            "PRODUCTION_URL",
        },
        "forbidden_secrets": {
            "RAILWAY_TOKEN",
            "RAILWAY_TOKEN_PRODUCTION",
        },
        "forbidden_variables": {
            "RAILWAY_PRODUCTION_ENVIRONMENT",
            "RAILWAY_SERVICE_NAME",
        },
        "forbidden_railway_url_variables": {
            "PRODUCTION_URL",
        },
    },
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


def _present(forbidden: set[str], present: set[str]) -> list[str]:
    return sorted(forbidden & present)


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


def _github_variables(environment: str) -> dict[str, str]:
    output = _run(
        ["gh", "variable", "list", "--env", environment, "--json", "name,value"]
    )
    variables = json.loads(output)
    return {
        str(variable.get("name") or ""): str(variable.get("value") or "")
        for variable in variables
        if variable.get("name")
    }


def _is_railway_url(value: str) -> bool:
    parsed = urlparse(value)
    host = parsed.netloc.lower()
    if not host:
        host = value.lower()
    return host.endswith(".railway.app") or ".railway.app/" in value.lower()


def _railway_url_variables(
    required_cloud_run_urls: set[str], variables: dict[str, str]
) -> list[str]:
    return sorted(
        name
        for name in required_cloud_run_urls
        if name in variables and _is_railway_url(variables[name])
    )


def _forbidden_result(
    environment: str,
    requirements: dict[str, set[str]],
    secrets: set[str],
    variables: dict[str, str],
) -> CheckResult:
    variable_names = set(variables)
    forbidden = [
        *[
            f"secret:{name}"
            for name in _present(requirements.get("forbidden_secrets", set()), secrets)
        ],
        *[
            f"variable:{name}"
            for name in _present(
                requirements.get("forbidden_variables", set()), variable_names
            )
        ],
        *[
            f"railway_url:{name}"
            for name in _railway_url_variables(
                requirements.get("forbidden_railway_url_variables", set()),
                variables,
            )
        ],
    ]
    return CheckResult(
        name=f"github.env.{environment}.legacy_railway",
        status="pass" if not forbidden else "fail",
        details={
            "forbidden": sorted(forbidden),
            "missing": sorted(forbidden),
        },
    )


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
    else:
        review_count = int(reviews.get("required_approving_review_count") or 0)
        if review_count != REQUIRED_APPROVING_REVIEW_COUNT:
            missing.append("required_approving_review_count=0")
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
    if payload.get("required_conversation_resolution", {}).get("enabled"):
        missing.append("required_conversation_resolution_disabled")

    return CheckResult(
        name=f"github.branch.{branch}.protection",
        status="pass" if not missing else "fail",
        details={
            "missing": missing,
            "pull_request_reviews": bool(reviews),
            "required_approving_review_count": int(
                reviews.get("required_approving_review_count") or 0
            ),
            "required_status_checks": sorted(contexts),
        },
    )


def _github_checks(repo: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    for environment, requirements in REQUIRED_GITHUB.items():
        secrets = _github_secret_names(environment)
        variables = _github_variables(environment)
        variable_names = set(variables)
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
                _missing(requirements["variables"], variable_names),
                len(variable_names),
            )
        )
        results.append(_forbidden_result(environment, requirements, secrets, variables))
        results.append(_github_environment_protection(repo, environment))
    for branch in sorted(PROTECTED_BRANCHES):
        results.append(_branch_protection(repo, branch))
    return results


def _repo(explicit: str | None) -> str:
    if explicit:
        return explicit
    return _run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]).strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=None, help="GitHub repo, e.g. owner/name")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    return parser.parse_args()


def _payload(repo: str, checks: list[CheckResult]) -> dict[str, Any]:
    failed = [check for check in checks if check.status != "pass"]
    return {
        "checks": [{"name": c.name, "status": c.status, "details": c.details} for c in checks],
        "repo": repo,
        "runtime": "gcp-cloud-run",
        "status": "fail" if failed else "pass",
    }


def main() -> int:
    args = _parse_args()
    try:
        repo = _repo(args.repo)
        checks = [*_github_checks(repo)]
    except (InfraError, json.JSONDecodeError) as exc:
        print(f"RELEASE INFRA CHECK FAILED: {exc}", file=sys.stderr)
        return 1

    payload = _payload(repo, checks)

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
