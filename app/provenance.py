"""Runtime build provenance for deployed Stargate Lite instances."""

from __future__ import annotations

import os

_SHA_ENV_KEYS = (
    "STARGATE_BUILD_SHA",
    "GIT_SHA",
    "SOURCE_VERSION",
    "COMMIT_SHA",
    "RAILWAY_GIT_COMMIT_SHA",
    "RAILWAY_GIT_COMMIT",
)

_BUILD_TIME_ENV_KEYS = (
    "STARGATE_BUILD_TIME",
    "BUILD_TIME",
    "RAILWAY_DEPLOYMENT_CREATED_AT",
)

_DEPLOYMENT_ENV_KEYS = (
    "STARGATE_DEPLOYMENT_ID",
    "RAILWAY_DEPLOYMENT_ID",
)

_ENVIRONMENT_ENV_KEYS = (
    "STARGATE_ENVIRONMENT",
    "ENVIRONMENT",
    "RAILWAY_ENVIRONMENT_NAME",
)


def _first_env(keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
    return None


def get_build_provenance() -> dict[str, str | None]:
    """Return deployment provenance exposed through health/version endpoints."""
    commit_sha = _first_env(_SHA_ENV_KEYS)
    return {
        "commit_sha": commit_sha,
        "commit_short": commit_sha[:12] if commit_sha else None,
        "build_time": _first_env(_BUILD_TIME_ENV_KEYS),
        "deployment_id": _first_env(_DEPLOYMENT_ENV_KEYS),
        "environment": _first_env(_ENVIRONMENT_ENV_KEYS),
    }
