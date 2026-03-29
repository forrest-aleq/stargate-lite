"""High-level artifact capabilities built on top of E2B sandboxes."""

from __future__ import annotations

import json
import shlex
from typing import Any, Protocol

from app.connectors.e2b_sandbox.artifact_scripts import build_chart_script, build_xlsx_script
from app.connectors.e2b_sandbox.document_artifact_scripts import build_docx_script
from app.connectors.e2b_sandbox.pdf_artifact_scripts import build_pdf_script
from app.connectors.e2b_sandbox.presentation_artifact_scripts import build_pptx_script
from app.errors import ExecutionError, ValidationError


class _ArtifactRuntime(Protocol):
    def _get_or_create_sandbox(self, args: dict[str, Any]) -> Any: ...
    def _sandbox_id(self, sandbox: Any) -> str | None: ...


def _require_list(args: dict[str, Any], key: str) -> list[Any]:
    value = args.get(key)
    if not isinstance(value, list) or not value:
        raise ValidationError(key, "Must be a non-empty array")
    return value


def _optional_list(args: dict[str, Any], key: str) -> list[Any] | None:
    value = args.get(key)
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValidationError(key, "Must be an array")
    return value


def _optional_str(args: dict[str, Any], key: str) -> str | None:
    value = args.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(key, "Must be a string")
    text = value.strip()
    return text or None


def _run_script(
    runtime: _ArtifactRuntime,
    args: dict[str, Any],
    *,
    script_source: str,
    script_path: str,
) -> dict[str, Any]:
    sandbox = runtime._get_or_create_sandbox(args)
    sandbox.files.write(script_path, script_source)
    timeout_raw = args.get("command_timeout_seconds", 0) or 0
    try:
        timeout = float(timeout_raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "command_timeout_seconds",
            "Must be zero or a positive number",
        ) from exc
    if timeout < 0:
        raise ValidationError("command_timeout_seconds", "Must be zero or a positive number")

    result = sandbox.commands.run(f"python3 {shlex.quote(script_path)}", timeout=timeout)
    exit_code = getattr(result, "exit_code", None)
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    if exit_code not in (0, None):
        raise ExecutionError(
            "Artifact generation failed inside E2B.",
            details={
                "service": "e2b",
                "sandbox_id": runtime._sandbox_id(sandbox),
                "script_path": script_path,
                "exit_code": exit_code,
                "stderr": str(stderr),
            },
        )
    try:
        payload = json.loads(str(stdout).strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise ExecutionError(
            "Artifact generation returned an unreadable payload.",
            details={
                "service": "e2b",
                "sandbox_id": runtime._sandbox_id(sandbox),
                "script_path": script_path,
                "stdout": str(stdout),
                "stderr": str(stderr),
            },
        ) from exc
    if not isinstance(payload, dict):
        raise ExecutionError(
            "Artifact generation returned an invalid payload shape.",
            details={"service": "e2b", "sandbox_id": runtime._sandbox_id(sandbox)},
        )
    payload["sandbox_id"] = runtime._sandbox_id(sandbox)
    return payload


class E2BArtifactMixin:
    """Artifact generation helpers exposed as first-class Stargate capabilities."""

    def build_xlsx_artifact(
        self: _ArtifactRuntime,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        del org_id, user_id
        sheets = _require_list(args, "sheets")
        spec = {
            "workbook_name": _optional_str(args, "workbook_name") or "aleq-workbook.xlsx",
            "path": _optional_str(args, "path"),
            "author": _optional_str(args, "author") or "Aleq",
            "sheets": sheets,
            "named_ranges": _optional_list(args, "named_ranges") or [],
        }
        payload = _run_script(
            self,
            args,
            script_source=build_xlsx_script(spec),
            script_path="/workspace/aleq_build_xlsx.py",
        )
        payload["artifact_kind"] = "spreadsheet"
        return payload

    def render_chart(
        self: _ArtifactRuntime,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        del org_id, user_id
        labels = _require_list(args, "labels")
        series = _require_list(args, "series")
        chart_type = (_optional_str(args, "chart_type") or "line").lower()
        if chart_type not in {"line", "bar", "column"}:
            raise ValidationError("chart_type", "Must be line, bar, or column")
        spec = {
            "file_name": _optional_str(args, "file_name") or "aleq-chart.svg",
            "path": _optional_str(args, "path"),
            "chart_type": chart_type,
            "title": _optional_str(args, "title") or "Aleq chart",
            "subtitle": _optional_str(args, "subtitle") or "",
            "x_axis_label": _optional_str(args, "x_axis_label") or "",
            "y_axis_label": _optional_str(args, "y_axis_label") or "",
            "labels": labels,
            "series": series,
            "width": args.get("width") or 960,
            "height": args.get("height") or 540,
        }
        payload = _run_script(
            self,
            args,
            script_source=build_chart_script(spec),
            script_path="/workspace/aleq_render_chart.py",
        )
        payload["artifact_kind"] = "report"
        return payload

    def build_docx_artifact(
        self: _ArtifactRuntime,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        del org_id, user_id
        spec = {
            "file_name": _optional_str(args, "file_name") or "aleq-document.docx",
            "path": _optional_str(args, "path"),
            "title": _optional_str(args, "title") or "Aleq document",
            "subtitle": _optional_str(args, "subtitle") or "",
            "author": _optional_str(args, "author") or "Aleq",
            "sections": _require_list(args, "sections"),
        }
        payload = _run_script(
            self,
            args,
            script_source=build_docx_script(spec),
            script_path="/workspace/aleq_build_docx.py",
        )
        payload["artifact_kind"] = "document"
        return payload

    def build_pptx_artifact(
        self: _ArtifactRuntime,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        del org_id, user_id
        spec = {
            "file_name": _optional_str(args, "file_name") or "aleq-deck.pptx",
            "path": _optional_str(args, "path"),
            "title": _optional_str(args, "title") or "Aleq presentation",
            "author": _optional_str(args, "author") or "Aleq",
            "slides": _require_list(args, "slides"),
        }
        payload = _run_script(
            self,
            args,
            script_source=build_pptx_script(spec),
            script_path="/workspace/aleq_build_pptx.py",
        )
        payload["artifact_kind"] = "presentation"
        return payload

    def build_pdf_artifact(
        self: _ArtifactRuntime,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        del org_id, user_id
        spec = {
            "file_name": _optional_str(args, "file_name") or "aleq-report.pdf",
            "path": _optional_str(args, "path"),
            "title": _optional_str(args, "title") or "Aleq report",
            "subtitle": _optional_str(args, "subtitle") or "",
            "author": _optional_str(args, "author") or "Aleq",
            "sections": _require_list(args, "sections"),
        }
        payload = _run_script(
            self,
            args,
            script_source=build_pdf_script(spec),
            script_path="/workspace/aleq_build_pdf.py",
        )
        payload["artifact_kind"] = "document"
        return payload
