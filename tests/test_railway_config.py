from __future__ import annotations

import json
from pathlib import Path


def test_production_railway_autodeploy_requires_manual_trigger_path() -> None:
    config = json.loads(Path("railway.json").read_text())

    assert config["environments"]["production"]["build"]["watchPatterns"] == [
        ".railway/manual-production-deploy-trigger"
    ]
