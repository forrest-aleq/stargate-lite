from __future__ import annotations

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
