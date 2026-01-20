#!/usr/bin/env python3
"""Pre-commit hook: Check that functions don't exceed line limits.

Reads configuration from guardian_config.toml if available.
"""

from __future__ import annotations

import ast
import sys
import tomllib
from pathlib import Path

# Defaults (overridden by config)
DEFAULT_MAX_LINES = 50
CONFIG_FILE = "guardian_config.toml"


def load_config() -> int:
    """Load configuration from TOML file."""
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        return DEFAULT_MAX_LINES

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    if limits := data.get("limits"):
        return limits.get("max_function_lines", DEFAULT_MAX_LINES)

    return DEFAULT_MAX_LINES


def count_function_lines(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count lines in a function."""
    if not node.body:
        return 0

    start_line = node.lineno
    end_line = node.end_lineno or start_line

    return end_line - start_line + 1


def check_file(filepath: str, max_lines: int) -> list[str]:
    """Check all functions in a file for size violations."""
    path = Path(filepath)
    if not path.exists() or path.suffix != ".py":
        return []

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []  # Let other tools handle syntax errors

    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            line_count = count_function_lines(node)
            if line_count > max_lines:
                violations.append(
                    f"  {filepath}:{node.lineno} "
                    f"'{node.name}()' has {line_count} lines (max {max_lines})"
                )

    return violations


def main() -> int:
    """Check all provided files."""
    if len(sys.argv) < 2:
        return 0

    max_lines = load_config()

    all_violations = []
    for filepath in sys.argv[1:]:
        violations = check_file(filepath, max_lines)
        all_violations.extend(violations)

    if all_violations:
        print(f"Functions exceeding {max_lines} lines:")
        for v in all_violations:
            print(v)
        print("\nExtract helper functions to reduce complexity.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
