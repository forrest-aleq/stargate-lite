#!/usr/bin/env python3
"""Check API contract quality for Pydantic models.

Validates that all public Pydantic models follow contract conventions:
- All fields have descriptions
- All models have docstrings
- Examples are provided for complex models

This runs as a pre-commit hook to catch contract issues early.

Usage:
    python scripts/check_api_contracts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_model_descriptions() -> list[str]:
    """Check that all public Pydantic models have proper descriptions."""
    from app import models

    violations: list[str] = []
    public_models = [
        name
        for name in dir(models)
        if not name.startswith("_")
        and isinstance(getattr(models, name), type)
        and hasattr(getattr(models, name), "model_fields")
    ]

    for model_name in public_models:
        model = getattr(models, model_name)

        # Check model docstring
        if not model.__doc__ or model.__doc__.strip() == "":
            violations.append(f"Model '{model_name}' is missing a docstring")

        # Check field descriptions
        for field_name, field_info in model.model_fields.items():
            if not field_info.description:
                violations.append(f"Field '{model_name}.{field_name}' is missing a description")

    return violations


def check_enum_descriptions() -> list[str]:
    """Check that all public enums have docstrings."""
    from enum import Enum

    from app import models

    violations: list[str] = []
    public_enums = [
        name
        for name in dir(models)
        if not name.startswith("_")
        and isinstance(getattr(models, name), type)
        and issubclass(getattr(models, name), Enum)
    ]

    for enum_name in public_enums:
        enum_cls = getattr(models, enum_name)
        if not enum_cls.__doc__ or enum_cls.__doc__.strip() == "":
            violations.append(f"Enum '{enum_name}' is missing a docstring")

    return violations


def check_openapi_examples() -> list[str]:
    """Check that key models have examples in their Config."""
    from app import models

    # Models that must have examples (used in API contracts)
    required_examples = [
        "ToolExecutionRequest",
        "ToolExecutionResponse",
        "ErrorResponse",
        "HealthResponse",
    ]

    violations: list[str] = []

    for model_name in required_examples:
        if not hasattr(models, model_name):
            continue

        model = getattr(models, model_name)
        config = getattr(model, "Config", None)
        if not config:
            violations.append(f"Model '{model_name}' is missing Config class with example")
            continue

        extra = getattr(config, "json_schema_extra", None)
        if not extra or "example" not in extra:
            violations.append(f"Model '{model_name}' is missing json_schema_extra example")

    return violations


def main() -> int:
    """Run all contract checks."""
    all_violations: list[str] = []

    all_violations.extend(check_model_descriptions())
    all_violations.extend(check_enum_descriptions())
    all_violations.extend(check_openapi_examples())

    if all_violations:
        print("=" * 60)
        print("API CONTRACT VIOLATIONS")
        print("=" * 60)
        for v in sorted(set(all_violations)):
            print(f"  {v}")
        print("=" * 60)
        print(f"{len(set(all_violations))} issue(s)")
        print("")
        print("Fix: Add Field(..., description='...') to all model fields")
        print("Fix: Add docstrings to all models and enums")
        return 1

    print("API contracts: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
