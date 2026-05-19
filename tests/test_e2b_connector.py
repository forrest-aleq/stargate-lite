"""Tests for the E2B sandbox capability substrate."""

from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any, ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.connectors.e2b_sandbox.base import E2BSandboxConnector


class FakeCommandResult:
    def __init__(self, command: str) -> None:
        self.command = command
        self.stdout = f"ran: {command}"
        self.stderr = ""
        self.exit_code = 0


class FakeCommandHandle:
    def __init__(self, sandbox: FakeSandbox, command: str) -> None:
        self.sandbox = sandbox
        self.command = command
        self.pid = sandbox.next_pid()
        sandbox.processes.append(
            {
                "pid": self.pid,
                "tag": None,
                "cmd": "/bin/bash",
                "args": ["-l", "-c", command],
                "envs": {},
                "cwd": None,
            }
        )
        self.disconnected = False

    def disconnect(self) -> None:
        self.disconnected = True


class FakeFiles:
    def __init__(self, sandbox: FakeSandbox) -> None:
        self.sandbox = sandbox

    def write(self, path: str, data: str | bytes) -> None:
        self.sandbox.file_store[path] = data

    def read(self, path: str) -> str | bytes:
        return self.sandbox.file_store[path]


class FakeCommands:
    def __init__(self, sandbox: FakeSandbox) -> None:
        self.sandbox = sandbox

    def run(self, command: str, background: bool = False, timeout: float = 0) -> Any:
        self.sandbox.last_timeout = timeout
        self.sandbox.last_command = command
        if background:
            return FakeCommandHandle(self.sandbox, command)
        return FakeCommandResult(command)

    def list(self) -> list[dict[str, Any]]:
        return list(self.sandbox.processes)

    def kill(self, pid: int) -> bool:
        before = len(self.sandbox.processes)
        self.sandbox.processes = [proc for proc in self.sandbox.processes if proc["pid"] != pid]
        return len(self.sandbox.processes) != before


class FakeSandbox:
    created_with: ClassVar[list[dict[str, Any]]] = []
    connected_ids: ClassVar[list[str]] = []
    file_store_by_id: ClassVar[dict[str, dict[str, str | bytes]]] = {}
    paused_state_by_id: ClassVar[dict[str, bool]] = {}
    timeout_by_id: ClassVar[dict[str, int]] = {}
    process_store_by_id: ClassVar[dict[str, list[dict[str, Any]]]] = {}
    snapshot_ids: ClassVar[list[str]] = []

    def __init__(self, sandbox_id: str, timeout: int = 3600, template: str | None = None) -> None:
        self.sandbox_id = sandbox_id
        self.timeout = self.timeout_by_id.get(sandbox_id, timeout)
        self.template = template
        self.file_store = self.file_store_by_id.setdefault(sandbox_id, {})
        self.files = FakeFiles(self)
        self.commands = FakeCommands(self)
        self.last_command: str | None = None
        self.last_timeout: float | None = None
        self.paused = self.paused_state_by_id.get(sandbox_id, False)
        self.processes = self.process_store_by_id.setdefault(sandbox_id, [])

    def next_pid(self) -> int:
        return 1000 + len(self.processes) + 1

    @classmethod
    def create(cls, **kwargs: Any) -> FakeSandbox:
        cls.created_with.append(kwargs)
        timeout = int(kwargs.get("timeout", 3600))
        template = kwargs.get("template")
        cls.timeout_by_id["sbx_created"] = timeout
        return cls("sbx_created", timeout=timeout, template=template)

    @classmethod
    def connect(cls, sandbox_id: str) -> FakeSandbox:
        cls.connected_ids.append(sandbox_id)
        return cls(sandbox_id)

    def get_info(self) -> dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "template": self.template,
            "paused": self.paused,
            "timeout_seconds": self.timeout,
        }

    def get_metrics(self) -> dict[str, Any]:
        return {"cpu_ms": 12, "memory_mb": 64}

    def get_timeout(self) -> int:
        return self.timeout

    def beta_pause(self) -> None:
        self.paused = True
        self.paused_state_by_id[self.sandbox_id] = True

    def set_timeout(self, timeout: int) -> None:
        self.timeout = timeout
        self.timeout_by_id[self.sandbox_id] = timeout

    def create_snapshot(self) -> dict[str, Any]:
        snapshot_id = f"snap_{len(self.snapshot_ids) + 1}"
        self.snapshot_ids.append(snapshot_id)
        return {"snapshot_id": snapshot_id}

    def is_running(self) -> bool:
        return not self.paused


def _connector(monkeypatch: Any) -> E2BSandboxConnector:
    monkeypatch.setenv("E2B_API_KEY", "test-key")
    monkeypatch.setattr("app.connectors.e2b_sandbox.base._load_sandbox_class", lambda: FakeSandbox)
    FakeSandbox.created_with.clear()
    FakeSandbox.connected_ids.clear()
    FakeSandbox.file_store_by_id.clear()
    FakeSandbox.paused_state_by_id.clear()
    FakeSandbox.timeout_by_id.clear()
    FakeSandbox.process_store_by_id.clear()
    FakeSandbox.snapshot_ids.clear()
    return E2BSandboxConnector()


def test_e2b_capabilities_registered() -> None:
    from app.registry import ALL_CAPABILITIES

    for capability_key in (
        "sandbox.ensure",
        "sandbox.python.run",
        "sandbox.python.run_background",
        "sandbox.bash.run",
        "sandbox.bash.run_background",
        "sandbox.file.write",
        "sandbox.file.read",
        "sandbox.command.list",
        "sandbox.command.kill",
        "sandbox.pause",
        "sandbox.timeout.set",
        "sandbox.snapshot.create",
        "sandbox.get_info",
    ):
        assert capability_key in ALL_CAPABILITIES
        assert ALL_CAPABILITIES[capability_key]["service"] == "e2b"


def test_e2b_schemas_registered() -> None:
    from app.schemas import SCHEMA_REGISTRY

    assert "sandbox.ensure" in SCHEMA_REGISTRY
    assert "sandbox.python.run" in SCHEMA_REGISTRY
    assert "sandbox.file.read" in SCHEMA_REGISTRY
    assert "sandbox.command.list" in SCHEMA_REGISTRY
    assert SCHEMA_REGISTRY["sandbox.python.run"].service == "e2b"


def test_ensure_creates_sandbox(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)

    result = connector.ensure(
        "org_1",
        "user_1",
        {
            "template": "aleq-finance-runtime",
            "timeout_seconds": 14400,
            "pause_on_timeout": True,
            "auto_resume": True,
        },
    )

    assert result["sandbox_id"] == "sbx_created"
    assert result["template"] == "aleq-finance-runtime"
    assert FakeSandbox.created_with[-1]["timeout"] == 14400
    assert FakeSandbox.created_with[-1]["lifecycle"] == {"on_timeout": "pause", "auto_resume": True}


def test_python_run_writes_script_and_executes(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)

    result = connector.run_python(
        "org_1",
        "user_1",
        {
            "sandbox_id": "sbx_existing",
            "code": "print('hello')",
            "path": "/workspace/test.py",
            "cwd": "/workspace",
            "env": {"MODE": "demo"},
        },
    )

    assert result["sandbox_id"] == "sbx_existing"
    assert result["ok"] is True
    assert "python3 /workspace/test.py" in result["command"]
    stored = FakeSandbox.file_store_by_id["sbx_existing"]["/workspace/test.py"]
    assert stored == "print('hello')"


def test_background_commands_list_kill_snapshot_and_timeout(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)

    background = connector.run_bash_background(
        "org_1",
        "user_1",
        {
            "sandbox_id": "sbx_existing",
            "command": "sleep 30",
        },
    )
    assert background["pid"] == 1001
    assert background["background"] is True

    processes = connector.list_commands("org_1", "user_1", {"sandbox_id": "sbx_existing"})
    assert processes["count"] == 1
    assert processes["commands"][0]["pid"] == 1001

    timeout = connector.set_timeout(
        "org_1",
        "user_1",
        {"sandbox_id": "sbx_existing", "timeout_seconds": 7200},
    )
    assert timeout["timeout_seconds"] == 7200

    info = connector.get_info("org_1", "user_1", {"sandbox_id": "sbx_existing"})
    assert info["timeout_seconds"] == 7200
    assert info["state"] == "running"
    assert info["paused"] is False

    snapshot = connector.create_snapshot("org_1", "user_1", {"sandbox_id": "sbx_existing"})
    assert snapshot["snapshot_id"] == "snap_1"

    killed = connector.kill_command(
        "org_1",
        "user_1",
        {"sandbox_id": "sbx_existing", "pid": 1001},
    )
    assert killed["killed"] is True


def test_file_write_and_read_base64(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)
    payload = base64.b64encode(b"abc123").decode("ascii")

    write_result = connector.write_file(
        "org_1",
        "user_1",
        {
            "sandbox_id": "sbx_existing",
            "path": "/workspace/blob.bin",
            "content": payload,
            "encoding": "base64",
        },
    )

    assert write_result["status"] == "written"

    read_result = connector.read_file(
        "org_1",
        "user_1",
        {
            "sandbox_id": "sbx_existing",
            "path": "/workspace/blob.bin",
            "encoding": "base64",
        },
    )

    assert read_result["content"] == payload
    assert read_result["size_bytes"] == 6


def test_pause_and_get_info(monkeypatch: Any) -> None:
    connector = _connector(monkeypatch)

    pause_result = connector.pause("org_1", "user_1", {"sandbox_id": "sbx_existing"})
    assert pause_result == {"sandbox_id": "sbx_existing", "status": "paused"}

    info_result = connector.get_info("org_1", "user_1", {"sandbox_id": "sbx_existing"})
    assert info_result["sandbox_id"] == "sbx_existing"
    assert info_result["info"]["paused"] is True
    assert info_result["state"] == "paused"
    assert info_result["paused"] is True
    assert info_result["metrics"]["memory_mb"] == 64
    assert info_result["running"] is False
