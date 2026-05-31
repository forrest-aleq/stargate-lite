from __future__ import annotations

import json
from pathlib import Path


def test_production_railway_autodeploy_requires_manual_trigger_path() -> None:
    config = json.loads(Path("railway.json").read_text())

    assert config["environments"]["production"]["build"]["watchPatterns"] == [
        ".railway/manual-production-deploy-trigger"
    ]


def test_production_deploy_advances_manual_trigger_before_upload() -> None:
    workflow = Path(".github/workflows/deploy-production.yml").read_text()

    trigger_write = ".railway/manual-production-deploy-trigger"
    upload = "retry_railway up --detach --json"

    assert "mkdir -p .railway" in workflow
    assert trigger_write in workflow
    assert workflow.index(trigger_write) < workflow.index(upload)
