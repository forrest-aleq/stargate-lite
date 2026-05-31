from __future__ import annotations

import json

from scripts import verify_release_infra as infra


def test_parse_names_table_uses_first_column() -> None:
    output = "PRODUCTION_API_KEY\t2026-05-18T07:28:07Z\nPRODUCTION_URL\tvalue\tdate\n"

    assert infra._parse_names_table(output) == {"PRODUCTION_API_KEY", "PRODUCTION_URL"}


def test_missing_is_sorted() -> None:
    assert infra._missing({"b", "a", "c"}, {"c"}) == ["a", "b"]


def test_result_marks_missing_as_failure() -> None:
    result = infra._result("github.env.production.variables", ["RAILWAY_SERVICE_NAME"], 1)

    assert result.status == "fail"
    assert result.details["missing"] == ["RAILWAY_SERVICE_NAME"]


def test_production_url_is_required_for_health_preflight(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(args: list[str]) -> str:
        calls.append(args)
        if args[:3] == ["gh", "secret", "list"]:
            return "PRODUCTION_API_KEY\tdate\nRAILWAY_TOKEN_PRODUCTION\tdate\n"
        if args[:3] == ["gh", "variable", "list"]:
            return (
                "RAILWAY_PROJECT_ID\tproject\tdate\n"
                "RAILWAY_PRODUCTION_ENVIRONMENT\tproduction\tdate\n"
                "RAILWAY_SERVICE_NAME\tstargate-lite\tdate\n"
            )
        if args[:2] == ["gh", "api"]:
            return json.dumps(
                {
                    "can_admins_bypass": False,
                    "deployment_branch_policy": {
                        "protected_branches": True,
                        "custom_branch_policies": False,
                    },
                    "protection_rules": [{"type": "branch_policy"}],
                }
            )
        raise AssertionError(args)

    monkeypatch.setattr(infra, "_run", fake_run)

    result = next(
        check
        for check in infra._github_checks("forrest-aleq/stargate-lite")
        if check.name == "github.env.production.variables"
    )

    assert result.status == "fail"
    assert result.details["missing"] == ["PRODUCTION_URL"]


def test_production_url_satisfies_health_preflight_requirement(monkeypatch) -> None:
    def fake_run(args: list[str]) -> str:
        if args[:3] == ["gh", "secret", "list"]:
            return "PRODUCTION_API_KEY\tdate\nRAILWAY_TOKEN_PRODUCTION\tdate\n"
        if args[:3] == ["gh", "variable", "list"]:
            return (
                "PRODUCTION_URL\thttps://stargate-lite-production.up.railway.app\tdate\n"
                "RAILWAY_PROJECT_ID\tproject\tdate\n"
                "RAILWAY_PRODUCTION_ENVIRONMENT\tproduction\tdate\n"
                "RAILWAY_SERVICE_NAME\tStargate Lite\tdate\n"
            )
        if args[:2] == ["gh", "api"]:
            return json.dumps(
                {
                    "can_admins_bypass": False,
                    "deployment_branch_policy": {
                        "protected_branches": True,
                        "custom_branch_policies": False,
                    },
                    "protection_rules": [{"type": "branch_policy"}],
                }
            )
        raise AssertionError(args)

    monkeypatch.setattr(infra, "_run", fake_run)

    result = next(
        check
        for check in infra._github_checks("forrest-aleq/stargate-lite")
        if check.name == "github.env.production.variables"
    )

    assert result.status == "pass"
    assert result.details["missing"] == []


def test_payload_fails_when_any_check_fails() -> None:
    checks = [
        infra.CheckResult("ok", "pass", {"missing": []}),
        infra.CheckResult("bad", "fail", {"missing": ["RAILWAY_SERVICE_NAME"]}),
    ]

    payload = infra._payload("forrest-aleq/stargate-lite", checks, "stargate-lite")

    assert payload["status"] == "fail"
    assert payload["runtime"] == "railway"
    assert payload["railway_service"] == "stargate-lite"


def test_branch_protection_accepts_zero_approval_release_lock(monkeypatch) -> None:
    payload = {
        "enforce_admins": {"enabled": True},
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "required_approving_review_count": 0,
        },
        "required_status_checks": {
            "contexts": ["Lint & Type Check", "Tests", "Security Scan", "Build Check"]
        },
        "required_linear_history": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
        "required_conversation_resolution": {"enabled": False},
    }
    monkeypatch.setattr(infra, "_run", lambda _: json.dumps(payload))

    result = infra._branch_protection("forrest-aleq/stargate-lite", "main")

    assert result.status == "pass"
    assert result.details["missing"] == []


def test_branch_protection_rejects_human_approval_requirement(monkeypatch) -> None:
    payload = {
        "enforce_admins": {"enabled": True},
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "required_approving_review_count": 1,
        },
        "required_status_checks": {
            "contexts": ["Lint & Type Check", "Tests", "Security Scan", "Build Check"]
        },
        "required_linear_history": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
        "required_conversation_resolution": {"enabled": False},
    }
    monkeypatch.setattr(infra, "_run", lambda _: json.dumps(payload))

    result = infra._branch_protection("forrest-aleq/stargate-lite", "main")

    assert result.status == "fail"
    assert result.details["missing"] == ["required_approving_review_count=0"]


def test_environment_protection_accepts_protected_branches_without_admin_bypass(
    monkeypatch,
) -> None:
    payload = {
        "can_admins_bypass": False,
        "deployment_branch_policy": {
            "protected_branches": True,
            "custom_branch_policies": False,
        },
        "protection_rules": [{"type": "branch_policy"}],
    }
    monkeypatch.setattr(infra, "_run", lambda _: json.dumps(payload))

    result = infra._github_environment_protection(
        "forrest-aleq/stargate-lite",
        "production",
    )

    assert result.status == "pass"
    assert result.details["missing"] == []


def test_environment_protection_rejects_admin_bypass_or_unprotected_deploys(
    monkeypatch,
) -> None:
    payload = {
        "can_admins_bypass": True,
        "deployment_branch_policy": {
            "protected_branches": False,
            "custom_branch_policies": True,
        },
        "protection_rules": [],
    }
    monkeypatch.setattr(infra, "_run", lambda _: json.dumps(payload))

    result = infra._github_environment_protection(
        "forrest-aleq/stargate-lite",
        "production",
    )

    assert result.status == "fail"
    assert result.details["missing"] == [
        "admins_cannot_bypass",
        "protected_branch_deployments",
        "custom_branch_policies_disabled",
        "branch_policy_rule",
    ]
