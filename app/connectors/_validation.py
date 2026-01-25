"""
Connector argument validation helpers.

Provides type-safe extraction of arguments from the args dict.
These helpers narrow types for mypy and raise clear errors for missing/invalid args.
"""

from typing import Any, TypeVar

T = TypeVar("T")


def require_str(args: dict[str, Any], key: str) -> str:
    """Extract a required string argument."""
    value = args.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} is required")
    return value


def require_int(args: dict[str, Any], key: str) -> int:
    """Extract a required integer argument."""
    value = args.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key} is required and must be an integer")
    return value


def require_float(args: dict[str, Any], key: str) -> float:
    """Extract a required float/number argument."""
    value = args.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} is required and must be a number")
    return float(value)


def optional_str(args: dict[str, Any], key: str, default: str | None = None) -> str | None:
    """Extract an optional string argument."""
    value = args.get(key)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def optional_int(args: dict[str, Any], key: str, default: int | None = None) -> int | None:
    """Extract an optional integer argument."""
    value = args.get(key)
    if value is None:
        return default
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def optional_bool(args: dict[str, Any], key: str, default: bool = False) -> bool:
    """Extract an optional boolean argument."""
    value = args.get(key)
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def optional_dict(
    args: dict[str, Any], key: str, default: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Extract an optional dict argument."""
    value = args.get(key)
    if value is None:
        return default if default is not None else {}
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a dictionary")
    return value


def optional_list(args: dict[str, Any], key: str) -> list[Any]:
    """Extract an optional list argument."""
    value = args.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value
