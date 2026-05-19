"""JSON-safe normalization helpers for E2B SDK objects."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any


def to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return to_jsonable(model_dump())

    dict_method = getattr(value, "dict", None)
    if callable(dict_method):
        return to_jsonable(dict_method())

    value_dict = getattr(value, "__dict__", None)
    if isinstance(value_dict, dict):
        clean = {key: item for key, item in value_dict.items() if not str(key).startswith("_")}
        if clean:
            return to_jsonable(clean)

    return str(value)


def extract_timeout_seconds(info: Any) -> int | None:
    info_json = to_jsonable(info)
    raw = None
    if isinstance(info_json, dict):
        raw = info_json.get("timeout") or info_json.get("timeout_seconds")
        if raw is None:
            end_at = info_json.get("end_at")
            started_at = info_json.get("started_at")
            if isinstance(end_at, str) and isinstance(started_at, str):
                try:
                    raw = int(
                        (
                            datetime.fromisoformat(end_at.replace("Z", "+00:00"))
                            - datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                        ).total_seconds()
                    )
                except ValueError:
                    raw = None
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def extract_state(info: Any) -> str | None:
    info_json = to_jsonable(info)
    if isinstance(info_json, dict):
        state = info_json.get("state")
        if isinstance(state, str) and state.strip():
            return state.strip().lower()
    return None


def is_paused(info: Any) -> bool | None:
    info_json = to_jsonable(info)
    if isinstance(info_json, dict):
        paused = info_json.get("paused")
        if isinstance(paused, bool):
            return paused
        state = info_json.get("state")
        if isinstance(state, str):
            normalized = state.strip().lower()
            if normalized == "paused":
                return True
            if normalized in {"running", "starting", "resuming"}:
                return False
    return None
