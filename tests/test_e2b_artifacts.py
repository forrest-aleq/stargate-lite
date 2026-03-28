"""Tests for high-level E2B artifact capabilities."""

from __future__ import annotations

import base64
import io
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, ClassVar

from cryptography.fernet import Fernet

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.connectors.e2b_sandbox.base import E2BSandboxConnector


class _Result:
    def __init__(self, stdout: str = "", stderr: str = "", exit_code: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


class _Files:
    def __init__(self, sandbox: _Sandbox) -> None:
        self._sandbox = sandbox

    def write(self, path: str, data: str | bytes) -> None:
        self._sandbox.store[path] = data

    def read(self, path: str) -> str | bytes:
        return self._sandbox.store[path]


class _Commands:
    def __init__(self, sandbox: _Sandbox) -> None:
        self._sandbox = sandbox

    def run(self, command: str, background: bool = False, timeout: float = 0) -> Any:
        del background, timeout
        parts = command.split()
        if len(parts) >= 2 and parts[0] == "python3":
            script_path = parts[1]
            source = self._sandbox.store[script_path]
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
                tmp.write(source if isinstance(source, str) else source.decode("utf-8"))
                tmp_path = tmp.name
            completed = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                check=False,
            )
            return _Result(
                stdout=completed.stdout,
                stderr=completed.stderr,
                exit_code=completed.returncode,
            )
        return _Result(stdout="", stderr="", exit_code=0)


class _Sandbox:
    store_by_id: ClassVar[dict[str, dict[str, str | bytes]]] = {}

    def __init__(self, sandbox_id: str) -> None:
        self.sandbox_id = sandbox_id
        self.store = self.store_by_id.setdefault(sandbox_id, {})
        self.files = _Files(self)
        self.commands = _Commands(self)

    @classmethod
    def create(cls, **_: Any) -> _Sandbox:
        return cls("sbx_artifact")

    @classmethod
    def connect(cls, sandbox_id: str, timeout: int | None = None) -> _Sandbox:
        del timeout
        return cls(sandbox_id)


def _connector(monkeypatch: Any) -> E2BSandboxConnector:
    monkeypatch.setenv("E2B_API_KEY", "test-key")
    monkeypatch.setattr("app.connectors.e2b_sandbox.base._load_sandbox_class", lambda: _Sandbox)
    _Sandbox.store_by_id.clear()
    return E2BSandboxConnector()


def test_artifact_capabilities_registered(monkeypatch: Any) -> None:
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    from app.registry import ALL_CAPABILITIES
    from app.schemas import SCHEMA_REGISTRY

    assert "artifact.xlsx.build" in ALL_CAPABILITIES
    assert "chart.render" in ALL_CAPABILITIES
    assert "artifact.docx.build" in ALL_CAPABILITIES
    assert "artifact.pptx.build" in ALL_CAPABILITIES
    assert "artifact.pdf.build" in ALL_CAPABILITIES
    assert "artifact.xlsx.build" in SCHEMA_REGISTRY
    assert "chart.render" in SCHEMA_REGISTRY
    assert "artifact.docx.build" in SCHEMA_REGISTRY
    assert "artifact.pptx.build" in SCHEMA_REGISTRY
    assert "artifact.pdf.build" in SCHEMA_REGISTRY


def test_build_xlsx_artifact_generates_workbook(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)
    result = connector.build_xlsx_artifact(
        "org_1",
        "user_1",
        {
            "workbook_name": "waterfall.xlsx",
            "path": "waterfall.xlsx",
            "sheets": [
                {
                    "name": "Waterfall",
                    "columns": ["Partner", "Distribution", "Promote %"],
                    "rows": [["GP", 1250000, 0.2], ["LP", 3750000, 0.8]],
                    "currency_columns": ["Distribution"],
                    "percent_columns": ["Promote %"],
                }
            ],
        },
    )

    assert result["artifact_kind"] == "spreadsheet"
    assert result["file_name"] == "waterfall.xlsx"
    assert result["sheet_count"] == 1
    payload = base64.b64decode(result["file_content"])
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        workbook = archive.read("xl/workbook.xml").decode("utf-8")
        shared = archive.read("xl/sharedStrings.xml").decode("utf-8")
        sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "Waterfall" in workbook
    assert "Partner" in shared
    assert "GP" in shared
    assert "autoFilter" in sheet


def test_render_chart_generates_svg(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)
    result = connector.render_chart(
        "org_1",
        "user_1",
        {
            "chart_type": "line",
            "path": "burn.svg",
            "title": "Monthly burn",
            "labels": ["Jan", "Feb", "Mar"],
            "series": [{"name": "Burn", "values": [320000, 295000, 310000]}],
        },
    )

    assert result["artifact_kind"] == "report"
    assert result["mime_type"] == "image/svg+xml"
    svg = base64.b64decode(result["file_content"]).decode("utf-8")
    assert "<svg" in svg
    assert "Monthly burn" in svg
    assert "Burn" in svg


def test_build_docx_artifact_generates_document(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)
    result = connector.build_docx_artifact(
        "org_1",
        "user_1",
        {
            "file_name": "board-update.docx",
            "path": "board-update.docx",
            "title": "Q1 board update",
            "subtitle": "Collections and burn review",
            "sections": [
                {
                    "heading": "Executive summary",
                    "paragraphs": [
                        "Revenue improved while AR aging widened during the quarter.",
                    ],
                    "bullets": [
                        "Net burn improved 11% month over month.",
                        "Three accounts now drive most of the overdue balance.",
                    ],
                    "table": {
                        "columns": ["Account", "Overdue"],
                        "rows": [["Apex", "$420K"], ["Northstar", "$310K"]],
                    },
                }
            ],
        },
    )

    assert result["artifact_kind"] == "document"
    assert (
        result["mime_type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    payload = base64.b64decode(result["file_content"])
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
        styles = archive.read("word/styles.xml").decode("utf-8")
    assert "Q1 board update" in document
    assert "Executive summary" in document
    assert "Northstar" in document
    assert "BodyText" in styles


def test_build_pptx_artifact_generates_deck(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)
    result = connector.build_pptx_artifact(
        "org_1",
        "user_1",
        {
            "file_name": "collections-review.pptx",
            "path": "collections-review.pptx",
            "title": "Collections review",
            "slides": [
                {
                    "title": "Collections posture",
                    "subtitle": "AR risk concentration",
                    "bullets": [
                        "Three enterprise accounts drive most overdue exposure.",
                        "Collections cycle slipped by five days month over month.",
                    ],
                    "metrics": [
                        {"label": "Overdue AR", "value": "$1.8M"},
                        {"label": "DSO", "value": "54 days"},
                    ],
                }
            ],
        },
    )

    assert result["artifact_kind"] == "presentation"
    assert (
        result["mime_type"]
        == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    payload = base64.b64decode(result["file_content"])
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        presentation = archive.read("ppt/presentation.xml").decode("utf-8")
        slide = archive.read("ppt/slides/slide1.xml").decode("utf-8")
    assert "sldMasterIdLst" in presentation
    assert "Collections posture" in slide
    assert "Overdue AR" in slide


def test_build_pdf_artifact_generates_pdf(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)
    result = connector.build_pdf_artifact(
        "org_1",
        "user_1",
        {
            "file_name": "board-brief.pdf",
            "path": "board-brief.pdf",
            "title": "Board brief",
            "subtitle": "Collections and runway review",
            "sections": [
                {
                    "heading": "Executive summary",
                    "paragraphs": [
                        "Collections remained the main drag on working capital during the month.",
                    ],
                    "bullets": [
                        "Overdue AR is concentrated in three accounts.",
                        (
                            "Cash remains above the board threshold if collections "
                            "land inside 21 days."
                        ),
                    ],
                    "table": {
                        "columns": ["Account", "Overdue"],
                        "rows": [["Apex", "$420K"], ["Northstar", "$310K"]],
                    },
                }
            ],
        },
    )

    assert result["artifact_kind"] == "document"
    assert result["mime_type"] == "application/pdf"
    assert result["page_count"] >= 1
    payload = base64.b64decode(result["file_content"])
    assert payload.startswith(b"%PDF-1.4")
    assert b"Board brief" in payload
    assert b"Executive summary" in payload
    assert b"Northstar" in payload
