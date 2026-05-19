from __future__ import annotations

import json

from scripts import verify_release_infra as infra


def test_parse_names_table_uses_first_column() -> None:
    output = "PRODUCTION_API_KEY\t2026-05-18T07:28:07Z\nPRODUCTION_URL\tvalue\tdate\n"

    assert infra._parse_names_table(output) == {"PRODUCTION_API_KEY", "PRODUCTION_URL"}


def test_missing_is_sorted() -> None:
    assert infra._missing({"b", "a", "c"}, {"c"}) == ["a", "b"]


def test_result_marks_missing_as_failure() -> None:
    result = infra._result("github.env.production.secrets", ["RAILWAY_TOKEN_PRODUCTION"], 1)

    assert result.status == "fail"
    assert result.details["missing"] == ["RAILWAY_TOKEN_PRODUCTION"]


def test_payload_fails_when_any_check_fails() -> None:
    checks = [
        infra.CheckResult("ok", "pass", {"missing": []}),
        infra.CheckResult("bad", "fail", {"missing": ["RAILWAY_TOKEN_STAGING"]}),
    ]

    payload = infra._payload("forrest-aleq/stargate-lite", checks, "stargate-lite", "Stargate Lite")

    assert payload["status"] == "fail"
    assert payload["railway_services"]["staging"] == "stargate-lite"


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
