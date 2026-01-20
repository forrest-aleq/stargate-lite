#!/usr/bin/env python3
"""Pre-commit hook: Check that Python files don't exceed line limits.

Reads configuration from guardian_config.toml if available.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

# Defaults (overridden by config)
DEFAULT_MAX_LINES = 500
CONFIG_FILE = "guardian_config.toml"


def load_config() -> tuple[int, dict[str, int]]:
    """Load configuration from TOML file."""
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        return DEFAULT_MAX_LINES, {}

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    max_lines = DEFAULT_MAX_LINES
    custom_limits: dict[str, int] = {}

    if limits := data.get("limits"):
        max_lines = limits.get("max_file_lines", DEFAULT_MAX_LINES)
        if custom := limits.get("custom_file_limits"):
            custom_limits = dict(custom)

    return max_lines, custom_limits


def get_limit_for_file(filepath: str, max_lines: int, custom_limits: dict[str, int]) -> int:
    """Get the line limit for a file (custom or default)."""
    for pattern, limit in custom_limits.items():
        if filepath.endswith(pattern):
            return limit
    return max_lines


def check_file(filepath: str, max_lines: int, custom_limits: dict[str, int]) -> bool:
    """Check if file exceeds line limit."""
    path = Path(filepath)
    if not path.exists() or path.suffix != ".py":
        return True

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return True  # Skip files we can't read

    line_count = len(lines)
    limit = get_limit_for_file(filepath, max_lines, custom_limits)

    if line_count > limit:
        print(f"FAIL {filepath}: {line_count} lines (max {limit})")
        return False

    return True


def main() -> int:
    """Check all provided files."""
    if len(sys.argv) < 2:
        return 0

    max_lines, custom_limits = load_config()

    failed = False
    for filepath in sys.argv[1:]:
        if not check_file(filepath, max_lines, custom_limits):
            failed = True

    if failed:
        print(f"\nFiles exceeding {max_lines} lines must be split into smaller modules.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
