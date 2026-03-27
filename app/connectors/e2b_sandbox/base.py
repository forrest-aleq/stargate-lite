"""E2B sandbox substrate for code execution and artifact work."""

from __future__ import annotations

import base64
import os
import shlex
from typing import Any, cast

from app.connectors.e2b_sandbox.serialization import (
    extract_state,
    extract_timeout_seconds,
    is_paused,
    to_jsonable,
)
from app.errors import ExecutionError, ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 60 * 60
_MAX_TIMEOUT_SECONDS = 24 * 60 * 60


def _load_sandbox_class() -> type[Any]:
    try:
        from e2b import Sandbox
    except ImportError as exc:
        raise ExecutionError(
            "E2B SDK is not installed in Stargate.",
            details={"service": "e2b"},
        ) from exc
    return cast(type[Any], Sandbox)


def _require_str(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(key, "Must be a non-empty string")
    return value.strip()


def _optional_str(args: dict[str, Any], key: str) -> str | None:
    value = args.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(key, "Must be a string")
    text = value.strip()
    return text or None


def _timeout_seconds(args: dict[str, Any]) -> int:
    raw = args.get("timeout_seconds", _DEFAULT_TIMEOUT_SECONDS)
    try:
        timeout = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError("timeout_seconds", "Must be an integer") from exc
    if timeout < 60:
        raise ValidationError("timeout_seconds", "Must be at least 60 seconds")
    return min(timeout, _MAX_TIMEOUT_SECONDS)


def _coerce_str_dict(args: dict[str, Any], key: str) -> dict[str, str]:
    raw = args.get(key)
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValidationError(key, "Must be an object of string key/value pairs")

    payload: dict[str, str] = {}
    for item_key, value in raw.items():
        if not isinstance(item_key, str) or not item_key.strip():
            raise ValidationError(key, "Keys must be non-empty strings")
        if not isinstance(value, str):
            raise ValidationError(key, f"Value for '{item_key}' must be a string")
        payload[item_key] = value
    return payload


def _coerce_env(args: dict[str, Any]) -> dict[str, str]:
    return _coerce_str_dict(args, "env")


def _coerce_metadata(args: dict[str, Any]) -> dict[str, str]:
    return _coerce_str_dict(args, "metadata")


def _bool_arg(args: dict[str, Any], key: str, default: bool) -> bool:
    value = args.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    raise ValidationError(key, "Must be a boolean")


def _lifecycle_config(args: dict[str, Any]) -> dict[str, Any] | None:
    on_timeout = _optional_str(args, "on_timeout")
    pause_on_timeout = args.get("pause_on_timeout")
    auto_resume = args.get("auto_resume")

    lifecycle: dict[str, Any] = {}
    if on_timeout:
        normalized = on_timeout.lower()
        if normalized not in {"kill", "pause"}:
            raise ValidationError("on_timeout", "Must be 'kill' or 'pause'")
        lifecycle["on_timeout"] = normalized
    elif pause_on_timeout is not None:
        lifecycle["on_timeout"] = "pause" if _bool_arg(args, "pause_on_timeout", False) else "kill"

    if auto_resume is not None:
        lifecycle["auto_resume"] = _bool_arg(args, "auto_resume", False)
        if lifecycle.get("auto_resume") and lifecycle.get("on_timeout") != "pause":
            raise ValidationError(
                "auto_resume",
                "auto_resume requires on_timeout='pause' or pause_on_timeout=true",
            )

    return lifecycle or None


def _build_shell_command(command: str, cwd: str | None, env: dict[str, str]) -> str:
    prefix: list[str] = []
    if cwd:
        prefix.append(f"cd {shlex.quote(cwd)}")
    if env:
        exports = " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items())
        prefix.append(f"export {exports}")
    prefix.append(command)
    return " && ".join(prefix)


def _normalize_text_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


class E2BSandboxConnector:
    """Small typed wrapper over E2B sandboxes for Stargate capabilities."""

    def __init__(self) -> None:
        self.api_key = os.getenv("E2B_API_KEY")

    def _ensure_enabled(self) -> None:
        if not self.api_key:
            raise ExecutionError(
                "E2B is not configured for this environment.",
                details={"service": "e2b", "missing_env": "E2B_API_KEY"},
            )

    def _get_or_create_sandbox(self, args: dict[str, Any]) -> Any:
        self._ensure_enabled()
        Sandbox = _load_sandbox_class()
        sandbox_id = _optional_str(args, "sandbox_id")
        timeout = _timeout_seconds(args)
        if sandbox_id:
            logger.info(
                "Connecting to existing E2B sandbox",
                sandbox_id=sandbox_id,
                timeout_seconds=timeout,
                log_event="e2b_connect_existing",
            )
            try:
                return Sandbox.connect(sandbox_id=sandbox_id, timeout=timeout)
            except TypeError:
                return Sandbox.connect(sandbox_id=sandbox_id)

        template = _optional_str(args, "template")
        create_kwargs: dict[str, Any] = {
            "timeout": timeout,
            "allow_internet_access": _bool_arg(args, "allow_internet_access", True),
        }
        if template:
            create_kwargs["template"] = template
        metadata = _coerce_metadata(args)
        if metadata:
            create_kwargs["metadata"] = metadata
        sandbox_env = _coerce_str_dict(args, "sandbox_env")
        if sandbox_env:
            create_kwargs["envs"] = sandbox_env
        lifecycle = _lifecycle_config(args)
        if lifecycle:
            create_kwargs["lifecycle"] = lifecycle

        try:
            sandbox = Sandbox.create(**create_kwargs)
        except TypeError:
            fallback_kwargs: dict[str, Any] = {"timeout": timeout}
            if template:
                fallback_kwargs["template"] = template
            sandbox = Sandbox.create(**fallback_kwargs)

        logger.info(
            "Created new E2B sandbox",
            sandbox_id=self._sandbox_id(sandbox),
            template=template,
            timeout_seconds=timeout,
            log_event="e2b_create_sandbox",
        )
        return sandbox

    def _sandbox_id(self, sandbox: Any) -> str | None:
        sandbox_id = getattr(sandbox, "sandbox_id", None) or getattr(sandbox, "id", None)
        return str(sandbox_id) if sandbox_id else None

    def _command_result(self, result: Any, *, sandbox: Any, command: str) -> dict[str, Any]:
        exit_code = getattr(result, "exit_code", None)
        stdout = _normalize_text_output(getattr(result, "stdout", ""))
        stderr = _normalize_text_output(getattr(result, "stderr", ""))
        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "ok": exit_code in (0, None),
        }

    def ensure(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        sandbox = self._get_or_create_sandbox(args)
        info_method = getattr(sandbox, "get_info", None)
        info = info_method() if callable(info_method) else None
        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "timeout_seconds": _timeout_seconds(args),
            "template": _optional_str(args, "template"),
            "connected": bool(_optional_str(args, "sandbox_id")),
            "lifecycle": _lifecycle_config(args),
            "info": to_jsonable(info),
        }

    def _run_command(
        self,
        args: dict[str, Any],
        *,
        command: str,
        extra: dict[str, Any] | None = None,
        background: bool = False,
    ) -> dict[str, Any]:
        sandbox = self._get_or_create_sandbox(args)
        shell_command = _build_shell_command(command, _optional_str(args, "cwd"), _coerce_env(args))
        raw_timeout = args.get("command_timeout_seconds", 0) or 0
        try:
            timeout = float(raw_timeout)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "command_timeout_seconds", "Must be zero or a positive number"
            ) from exc
        if timeout < 0:
            raise ValidationError("command_timeout_seconds", "Must be zero or a positive number")
        result = sandbox.commands.run(
            shell_command,
            background=background,
            timeout=timeout,
        )
        if background:
            pid = int(getattr(result, "pid", 0) or 0)
            disconnect = getattr(result, "disconnect", None)
            if callable(disconnect):
                disconnect()
            payload: dict[str, Any] = {
                "sandbox_id": self._sandbox_id(sandbox),
                "command": shell_command,
                "pid": pid,
                "ok": True,
                "background": True,
            }
            if extra:
                payload.update(extra)
            return payload
        payload = self._command_result(result, sandbox=sandbox, command=shell_command)
        payload["background"] = False
        if extra:
            payload.update(extra)
        return payload

    def run_python(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        code = _require_str(args, "code")
        file_path = _optional_str(args, "path") or "/workspace/aleq_script.py"
        sandbox = self._get_or_create_sandbox(args)
        sandbox.files.write(file_path, code)
        return self._run_command(
            args,
            command=f"python3 {shlex.quote(file_path)}",
            extra={"path": file_path},
        )

    def run_python_background(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        del org_id, user_id
        code = _require_str(args, "code")
        file_path = _optional_str(args, "path") or "/workspace/aleq_script.py"
        sandbox = self._get_or_create_sandbox(args)
        sandbox.files.write(file_path, code)
        return self._run_command(
            args,
            command=f"python3 {shlex.quote(file_path)}",
            extra={"path": file_path},
            background=True,
        )

    def run_bash(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        command = _require_str(args, "command")
        return self._run_command(args, command=command)

    def run_bash_background(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        del org_id, user_id
        command = _require_str(args, "command")
        return self._run_command(args, command=command, background=True)

    def write_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        sandbox = self._get_or_create_sandbox(args)
        path = _require_str(args, "path")
        content = _require_str(args, "content")
        encoding = (_optional_str(args, "encoding") or "text").lower()
        if encoding not in {"text", "base64"}:
            raise ValidationError("encoding", "Must be 'text' or 'base64'")

        data: str | bytes
        if encoding == "base64":
            try:
                data = base64.b64decode(content)
            except ValueError as exc:
                raise ValidationError("content", "Invalid base64 payload") from exc
        else:
            data = content

        sandbox.files.write(path, data)
        size_bytes = len(data) if isinstance(data, bytes) else len(data.encode("utf-8"))
        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "path": path,
            "encoding": encoding,
            "size_bytes": size_bytes,
            "status": "written",
        }

    def read_file(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        sandbox = self._get_or_create_sandbox(args)
        path = _require_str(args, "path")
        encoding = (_optional_str(args, "encoding") or "text").lower()
        if encoding not in {"text", "base64"}:
            raise ValidationError("encoding", "Must be 'text' or 'base64'")

        raw = sandbox.files.read(path)
        if isinstance(raw, str):
            text = raw
            data = raw.encode("utf-8")
        elif isinstance(raw, bytes):
            text = raw.decode("utf-8", errors="replace")
            data = raw
        else:
            text = str(raw)
            data = text.encode("utf-8")

        content = base64.b64encode(data).decode("ascii") if encoding == "base64" else text
        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "path": path,
            "encoding": encoding,
            "content": content,
            "size_bytes": len(data),
        }

    def pause(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        sandbox = self._get_or_create_sandbox(args)
        pause_method = getattr(sandbox, "beta_pause", None) or getattr(sandbox, "pause", None)
        if not callable(pause_method):
            raise ExecutionError(
                "This E2B SDK version does not expose pause support.",
                details={"service": "e2b", "sandbox_id": self._sandbox_id(sandbox)},
            )
        pause_method()
        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "status": "paused",
        }

    def set_timeout(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        sandbox = self._get_or_create_sandbox(args)
        timeout = _timeout_seconds(args)
        set_timeout = getattr(sandbox, "set_timeout", None)
        if not callable(set_timeout):
            raise ExecutionError(
                "This E2B SDK version does not expose timeout updates.",
                details={"service": "e2b", "sandbox_id": self._sandbox_id(sandbox)},
            )
        set_timeout(timeout)
        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "timeout_seconds": timeout,
            "status": "updated",
        }

    def create_snapshot(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        sandbox = self._get_or_create_sandbox(args)
        create_snapshot = getattr(sandbox, "create_snapshot", None)
        if not callable(create_snapshot):
            raise ExecutionError(
                "This E2B SDK version does not expose snapshot creation.",
                details={"service": "e2b", "sandbox_id": self._sandbox_id(sandbox)},
            )
        snapshot = create_snapshot()
        snapshot_id = None
        if isinstance(snapshot, dict):
            snapshot_id = snapshot.get("id") or snapshot.get("snapshot_id")
        else:
            snapshot_id = getattr(snapshot, "id", None) or getattr(snapshot, "snapshot_id", None)
        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "snapshot_id": str(snapshot_id) if snapshot_id else None,
            "snapshot": to_jsonable(snapshot),
        }

    def list_commands(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        sandbox = self._get_or_create_sandbox(args)
        list_method = getattr(sandbox.commands, "list", None)
        if not callable(list_method):
            raise ExecutionError(
                "This E2B SDK version does not expose process listing.",
                details={"service": "e2b", "sandbox_id": self._sandbox_id(sandbox)},
            )
        processes = list_method()
        process_rows = to_jsonable(processes)
        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "commands": process_rows,
            "processes": process_rows,
            "count": len(process_rows) if isinstance(process_rows, list) else None,
        }

    def kill_command(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        sandbox = self._get_or_create_sandbox(args)
        raw_pid = args.get("pid")
        if raw_pid is None:
            raise ValidationError("pid", "Must be an integer")
        try:
            pid = int(raw_pid)
        except (TypeError, ValueError) as exc:
            raise ValidationError("pid", "Must be an integer") from exc
        kill_method = getattr(sandbox.commands, "kill", None)
        if not callable(kill_method):
            raise ExecutionError(
                "This E2B SDK version does not expose process termination.",
                details={"service": "e2b", "sandbox_id": self._sandbox_id(sandbox)},
            )
        killed = bool(kill_method(pid))
        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "pid": pid,
            "killed": killed,
        }

    def get_info(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        del org_id, user_id
        sandbox = self._get_or_create_sandbox(args)
        info_method = getattr(sandbox, "get_info", None)
        metrics_method = getattr(sandbox, "get_metrics", None)
        running_method = getattr(sandbox, "is_running", None)
        info = info_method() if callable(info_method) else None
        info_json = to_jsonable(info)
        paused = is_paused(info)
        running = running_method() if callable(running_method) else None
        if running is None and paused is not None:
            running = not paused
        state = extract_state(info)
        if state is None:
            if paused is True:
                state = "paused"
            elif running is True:
                state = "running"

        return {
            "sandbox_id": self._sandbox_id(sandbox),
            "info": info_json,
            "metrics": to_jsonable(metrics_method()) if callable(metrics_method) else None,
            "state": state,
            "paused": paused,
            "timeout_seconds": extract_timeout_seconds(info) or _timeout_seconds(args),
            "running": running,
        }
