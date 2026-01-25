#!/usr/bin/env python3
"""
Release validation pre-commit hook.

Enforces release engineering rules:
1. VERSION in app/main.py must be valid semver
2. If VERSION changed, CHANGELOG.md must also be updated
3. CHANGELOG.md must have an entry for the current version

See docs/RELEASE_GUIDE.md for full release process.
"""

import re
import subprocess
import sys
from pathlib import Path

# Paths
ROOT = Path(__file__).parent.parent
MAIN_PY = ROOT / "app" / "main.py"
CHANGELOG = ROOT / "CHANGELOG.md"

# Semver pattern (allows 0.x.x pre-release versions)
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$")


def get_version_from_main() -> str | None:
    """Extract VERSION from app/main.py."""
    content = MAIN_PY.read_text()
    match = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    return match.group(1) if match else None


def get_staged_files() -> set[str]:
    """Get list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()


def version_in_changelog(version: str) -> bool:
    """Check if version has an entry in CHANGELOG.md."""
    if not CHANGELOG.exists():
        return False
    content = CHANGELOG.read_text()
    # Look for [version] or ## [version] patterns
    return f"[{version}]" in content


def get_previous_version() -> str | None:
    """Get VERSION from the last commit."""
    result = subprocess.run(
        ["git", "show", "HEAD:app/main.py"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        return None
    match = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', result.stdout, re.MULTILINE)
    return match.group(1) if match else None


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # Get current version
    version = get_version_from_main()
    if not version:
        errors.append("ERROR: VERSION not found in app/main.py")
        errors.append('  Add: VERSION = "0.9.0" at the top of the file')
        print("\n".join(errors))
        return 1

    # Validate semver format
    if not SEMVER_PATTERN.match(version):
        errors.append(f"ERROR: Invalid version format: {version}")
        errors.append("  Must be semantic version: MAJOR.MINOR.PATCH (e.g., 0.9.0, 1.0.0)")
        print("\n".join(errors))
        return 1

    # Get staged files
    staged = get_staged_files()

    # Check if version changed
    previous_version = get_previous_version()
    version_changed = previous_version and previous_version != version

    if version_changed:
        print(f"Version change detected: {previous_version} -> {version}")

        # If version changed, CHANGELOG must be updated
        if "CHANGELOG.md" not in staged:
            errors.append("ERROR: Version changed but CHANGELOG.md not updated")
            errors.append("  When bumping VERSION, you MUST update CHANGELOG.md")
            errors.append("  See docs/RELEASE_GUIDE.md for changelog format")

    # Check if CHANGELOG has entry for current version
    if not version_in_changelog(version):
        if version_changed:
            errors.append(f"ERROR: CHANGELOG.md missing entry for version {version}")
            errors.append(f"  Add a section: ## [{version}] - YYYY-MM-DD")
        else:
            warnings.append(f"WARNING: CHANGELOG.md missing entry for version {version}")
            warnings.append("  Consider adding a changelog entry before release")

    # Check for common mistakes
    if "app/main.py" in staged and version_changed:
        # Version bumped - remind about release process
        print(f"\nRelease checklist for v{version}:")
        print("  [ ] CHANGELOG.md updated")
        print("  [ ] Tests pass (make test)")
        print("  [ ] No new Sentry errors in staging")
        print("  [ ] See docs/RELEASE_GUIDE.md for full process")

    # Print results
    if warnings:
        print("\n".join(warnings))

    if errors:
        print("\n".join(errors))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
