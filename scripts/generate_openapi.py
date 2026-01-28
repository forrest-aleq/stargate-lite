#!/usr/bin/env python3
"""Generate OpenAPI specification from FastAPI app.

This script exports the OpenAPI spec to a JSON file that serves as
the source of truth for API contracts. The spec is committed to the
repository and used by N3 to generate TypeScript types.

Usage:
    python scripts/generate_openapi.py          # Generate spec
    python scripts/generate_openapi.py --check  # Check if spec is up to date

Exit codes:
    0: Success (or spec is up to date in --check mode)
    1: Spec is out of date (--check mode only)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_openapi_spec() -> dict:
    """Generate OpenAPI spec from FastAPI app.

    Ensures all contract-critical schemas are included even if they're
    not directly referenced by endpoints (e.g., union response types).
    """
    from app.main import app
    from app.models import ToolExecutionResponse

    spec = app.openapi()

    # Ensure ToolExecutionResponse is in the schema (used in execute endpoint
    # but not automatically included due to union type response)
    schemas = spec.setdefault("components", {}).setdefault("schemas", {})
    if "ToolExecutionResponse" not in schemas:
        schemas["ToolExecutionResponse"] = ToolExecutionResponse.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )

    return spec


def normalize_spec(spec: dict) -> str:
    """Normalize spec for consistent comparison.

    Sorts keys and uses consistent indentation to avoid
    spurious diffs from key ordering changes.
    """
    return json.dumps(spec, indent=2, sort_keys=True, default=str)


def main() -> int:
    """Generate or check OpenAPI specification."""
    check_mode = "--check" in sys.argv
    output_path = project_root / "openapi.json"

    # Generate current spec
    spec = get_openapi_spec()
    current_content = normalize_spec(spec)

    if check_mode:
        # Check if existing spec matches
        if not output_path.exists():
            print("ERROR: openapi.json does not exist.")
            print("Run 'python scripts/generate_openapi.py' to generate it.")
            return 1

        existing_content = output_path.read_text()

        if existing_content.strip() != current_content.strip():
            print("ERROR: openapi.json is out of date.")
            print("Run 'python scripts/generate_openapi.py' to regenerate it.")
            print("")
            print("Hint: If you modified Pydantic models or FastAPI endpoints,")
            print("you must regenerate the OpenAPI spec before committing.")
            return 1

        print("OK: openapi.json is up to date")
        return 0

    # Write spec to file
    output_path.write_text(current_content + "\n")
    print(f"Generated {output_path}")
    print(f"  Version: {spec.get('info', {}).get('version', 'unknown')}")
    print(f"  Paths: {len(spec.get('paths', {}))}")
    print(f"  Schemas: {len(spec.get('components', {}).get('schemas', {}))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
