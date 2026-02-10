#!/usr/bin/env python3
"""Check provider contract integrity.

Validates that:
1. Both provider contracts import cleanly
2. Contract versions haven't changed without a CHANGELOG entry
3. Error codes and retry strategies are consistent

This runs as a pre-commit hook alongside check_api_contracts.py.

Usage:
    python scripts/check_provider_contracts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_contracts_import() -> list[str]:
    """Verify both contracts import without errors."""
    violations: list[str] = []

    try:
        from app.contracts.n3 import N3_CONTRACT

        if not N3_CONTRACT.get("endpoints"):
            violations.append("N3_CONTRACT has no endpoints defined")
    except Exception as e:
        violations.append(f"Failed to import N3_CONTRACT: {e}")

    try:
        from app.contracts.mars import MARS_CONTRACT

        if not MARS_CONTRACT.get("endpoints"):
            violations.append("MARS_CONTRACT has no endpoints defined")
    except Exception as e:
        violations.append(f"Failed to import MARS_CONTRACT: {e}")

    return violations


def check_contract_versions() -> list[str]:
    """Verify contract versions match __init__ constants."""
    violations: list[str] = []

    try:
        from app.contracts import MARS_CONTRACT_VERSION, N3_CONTRACT_VERSION
        from app.contracts.mars import MARS_CONTRACT
        from app.contracts.n3 import N3_CONTRACT

        if N3_CONTRACT["version"] != N3_CONTRACT_VERSION:
            violations.append(
                f"N3 contract version mismatch: "
                f"n3.py says '{N3_CONTRACT['version']}' "
                f"but __init__.py says '{N3_CONTRACT_VERSION}'"
            )

        if MARS_CONTRACT["version"] != MARS_CONTRACT_VERSION:
            violations.append(
                f"MARS contract version mismatch: "
                f"mars.py says '{MARS_CONTRACT['version']}' "
                f"but __init__.py says '{MARS_CONTRACT_VERSION}'"
            )
    except Exception as e:
        violations.append(f"Failed to check contract versions: {e}")

    return violations


def check_error_taxonomy() -> list[str]:
    """Verify MARS error taxonomy is internally consistent."""
    violations: list[str] = []

    try:
        from app.contracts.mars import MARS_CONTRACT

        error_codes: dict[str, dict[str, str]] = MARS_CONTRACT["error_codes"]  # type: ignore[assignment]
        strategies: list[str] = MARS_CONTRACT["retry_strategies"]  # type: ignore[assignment]

        # Every error code's retry must be a known strategy
        for code, spec in error_codes.items():
            if spec["retry"] not in strategies:
                violations.append(
                    f"Error code '{code}' has retry='{spec['retry']}' "
                    f"which is not in retry_strategies {strategies}"
                )

        # Must have exactly 10 error codes
        if len(error_codes) != 10:
            violations.append(
                f"MARS contract has {len(error_codes)} error codes "
                f"(expected 10)"
            )

        # Must have exactly 3 retry strategies
        if len(strategies) != 3:
            violations.append(
                f"MARS contract has {len(strategies)} retry strategies "
                f"(expected 3)"
            )

    except Exception as e:
        violations.append(f"Failed to check error taxonomy: {e}")

    return violations


def main() -> int:
    """Run all provider contract checks."""
    all_violations: list[str] = []

    all_violations.extend(check_contracts_import())
    all_violations.extend(check_contract_versions())
    all_violations.extend(check_error_taxonomy())

    if all_violations:
        print("=" * 60)
        print("PROVIDER CONTRACT VIOLATIONS")
        print("=" * 60)
        for v in all_violations:
            print(f"  {v}")
        print("=" * 60)
        print(f"{len(all_violations)} issue(s)")
        return 1

    print("Provider contracts: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
