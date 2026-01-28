"""
Pytest configuration and fixtures for Stargate Lite tests.

This file sets up environment variables needed for testing BEFORE any
imports that might trigger ddtrace/dd_core initialization.
"""

import os

# Set dd_core environment variables FIRST to prevent KeyError
# This must happen before any imports that might trigger ddtrace
os.environ.setdefault("FILTER_THIRD_PARTY_LIB", "false")
os.environ.setdefault("DD_TRACE_ENABLED", "false")
os.environ.setdefault("DD_PATCH_MODULES", "none")

# Now safe to import pytest
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def reset_dd_env() -> None:
    """Ensure dd_core environment variables are set for each test."""
    os.environ.setdefault("FILTER_THIRD_PARTY_LIB", "false")
