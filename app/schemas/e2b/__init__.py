"""E2B sandbox capability schemas."""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    UsageExample,
    WorkflowHints,
)

SANDBOX_ENSURE = CapabilitySchema(
    capability_key="sandbox.ensure",
    service="e2b",
    category="sandbox",
    description="Create or reconnect to a reusable sandbox",
    description_detailed=(
        "Creates a new E2B sandbox or reconnects to an existing one when sandbox_id is "
        "provided. Use this to establish a long-lived execution substrate before running "
        "code, generating files, or pausing work for later."
    ),
    parameters={
        "sandbox_id": ParameterSchema(
            type="string",
            required=False,
            description="Existing sandbox ID to reconnect to",
        ),
        "template": ParameterSchema(
            type="string",
            required=False,
            description="Optional E2B template name for preinstalled tools",
            example="aleq-finance-runtime",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="String metadata tags stored on the sandbox",
        ),
        "sandbox_env": ParameterSchema(
            type="object",
            required=False,
            description="Environment variables applied when the sandbox is created",
        ),
        "allow_internet_access": ParameterSchema(
            type="boolean",
            required=False,
            description="Whether the sandbox can reach the internet",
            default=True,
        ),
        "on_timeout": ParameterSchema(
            type="string",
            required=False,
            description="Lifecycle behavior when timeout is reached",
            enum=["kill", "pause"],
        ),
        "pause_on_timeout": ParameterSchema(
            type="boolean",
            required=False,
            description="Convenience alias for on_timeout='pause'",
        ),
        "auto_resume": ParameterSchema(
            type="boolean",
            required=False,
            description="Automatically resume paused sandboxes when reconnecting",
        ),
        "timeout_seconds": ParameterSchema(
            type="integer",
            required=False,
            description="Requested sandbox lifetime in seconds",
            default=3600,
            example=14400,
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "timeout_seconds": ReturnFieldSchema(
            type="integer", description="Requested timeout in seconds"
        ),
        "template": ReturnFieldSchema(type="string", description="Resolved template name"),
        "connected": ReturnFieldSchema(
            type="boolean", description="True when reconnecting to an existing sandbox"
        ),
        "lifecycle": ReturnFieldSchema(type="object", description="Resolved lifecycle policy"),
        "info": ReturnFieldSchema(type="object", description="Raw sandbox info payload"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Sandbox runtime is not configured or unavailable",
            recovery_hint="Verify E2B_API_KEY and E2B service availability",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Sandbox arguments are malformed",
            recovery_hint="Provide valid timeout_seconds and string fields",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=[
            "sandbox.file.write",
            "sandbox.python.run",
            "sandbox.bash.run",
            "sandbox.pause",
        ],
    ),
    idempotent=False,
    has_side_effects=True,
)

SANDBOX_PYTHON_RUN = CapabilitySchema(
    capability_key="sandbox.python.run",
    service="e2b",
    category="execution",
    description="Run Python inside an isolated sandbox",
    description_detailed=(
        "Writes Python source into the sandbox and executes it with python3. Use for data "
        "analysis, spreadsheet generation, file transformation, and artifact creation."
    ),
    parameters={
        "code": ParameterSchema(
            type="string",
            required=True,
            description="Python source code to execute",
        ),
        "sandbox_id": ParameterSchema(
            type="string",
            required=False,
            description="Existing sandbox ID to reuse",
        ),
        "path": ParameterSchema(
            type="string",
            required=False,
            description="Destination path for the temporary script",
            default="/workspace/aleq_script.py",
        ),
        "cwd": ParameterSchema(
            type="string",
            required=False,
            description="Working directory inside the sandbox",
        ),
        "env": ParameterSchema(
            type="object",
            required=False,
            description="String environment variables to inject into the command",
        ),
        "template": ParameterSchema(
            type="string",
            required=False,
            description="Template to use when a new sandbox is created",
        ),
        "timeout_seconds": ParameterSchema(
            type="integer",
            required=False,
            description="Sandbox lifetime if creating a new instance",
            default=3600,
        ),
        "command_timeout_seconds": ParameterSchema(
            type="number",
            required=False,
            description="How long to keep the command connection open",
            default=0,
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "command": ReturnFieldSchema(type="string", description="Executed shell command"),
        "path": ReturnFieldSchema(type="string", description="Script path in sandbox"),
        "stdout": ReturnFieldSchema(type="string", description="Standard output"),
        "stderr": ReturnFieldSchema(type="string", description="Standard error"),
        "exit_code": ReturnFieldSchema(type="integer", description="Process exit code"),
        "ok": ReturnFieldSchema(type="boolean", description="True when exit_code is zero"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Code or execution arguments are malformed",
            recovery_hint="Provide code and valid string/object arguments",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Sandbox execution failed before returning a result",
            recovery_hint="Inspect stderr and sandbox lifecycle state",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.ensure", "sandbox.file.write"],
        typically_followed_by=["sandbox.file.read", "sandbox.pause"],
        related_capabilities=["sandbox.bash.run"],
    ),
    examples=[
        UsageExample(
            description="Generate a CSV from in-sandbox data",
            args={
                "sandbox_id": "sbx_123",
                "code": (
                    "from pathlib import Path\\n"
                    "Path('/workspace/out.txt').write_text('ok')\\n"
                    "print('done')"
                ),
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

SANDBOX_PYTHON_RUN_BACKGROUND = CapabilitySchema(
    capability_key="sandbox.python.run_background",
    service="e2b",
    category="execution",
    description="Start Python inside an isolated sandbox and leave it running",
    description_detailed=(
        "Writes Python source into the sandbox, starts it in the background, and returns "
        "a process ID for later inspection or termination."
    ),
    parameters=SANDBOX_PYTHON_RUN.parameters,
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "command": ReturnFieldSchema(type="string", description="Executed shell command"),
        "path": ReturnFieldSchema(type="string", description="Script path in sandbox"),
        "pid": ReturnFieldSchema(type="integer", description="Background process ID"),
        "ok": ReturnFieldSchema(type="boolean", description="True when the command started"),
        "background": ReturnFieldSchema(type="boolean", description="Always true"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.ensure", "sandbox.file.write"],
        typically_followed_by=["sandbox.command.list", "sandbox.command.kill", "sandbox.pause"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SANDBOX_BASH_RUN = CapabilitySchema(
    capability_key="sandbox.bash.run",
    service="e2b",
    category="execution",
    description="Run a shell command inside an isolated sandbox",
    parameters={
        "command": ParameterSchema(
            type="string",
            required=True,
            description="Shell command to execute",
            example="ls -la /tmp",
        ),
        "sandbox_id": ParameterSchema(
            type="string",
            required=False,
            description="Existing sandbox ID to reuse",
        ),
        "cwd": ParameterSchema(
            type="string",
            required=False,
            description="Working directory inside the sandbox",
        ),
        "env": ParameterSchema(
            type="object",
            required=False,
            description="String environment variables to inject into the command",
        ),
        "template": ParameterSchema(
            type="string",
            required=False,
            description="Template to use when a new sandbox is created",
        ),
        "timeout_seconds": ParameterSchema(
            type="integer",
            required=False,
            description="Sandbox lifetime if creating a new instance",
            default=3600,
        ),
        "command_timeout_seconds": ParameterSchema(
            type="number",
            required=False,
            description="How long to keep the command connection open",
            default=0,
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "command": ReturnFieldSchema(type="string", description="Executed shell command"),
        "stdout": ReturnFieldSchema(type="string", description="Standard output"),
        "stderr": ReturnFieldSchema(type="string", description="Standard error"),
        "exit_code": ReturnFieldSchema(type="integer", description="Process exit code"),
        "ok": ReturnFieldSchema(type="boolean", description="True when exit_code is zero"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Command or execution arguments are malformed",
            recovery_hint="Provide a non-empty command string and valid optional args",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.ensure"],
        typically_followed_by=["sandbox.file.read", "sandbox.pause"],
        related_capabilities=["sandbox.python.run"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SANDBOX_BASH_RUN_BACKGROUND = CapabilitySchema(
    capability_key="sandbox.bash.run_background",
    service="e2b",
    category="execution",
    description="Start a shell command in the sandbox and keep it running",
    parameters=SANDBOX_BASH_RUN.parameters,
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "command": ReturnFieldSchema(type="string", description="Executed shell command"),
        "pid": ReturnFieldSchema(type="integer", description="Background process ID"),
        "ok": ReturnFieldSchema(type="boolean", description="True when the command started"),
        "background": ReturnFieldSchema(type="boolean", description="Always true"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.ensure"],
        typically_followed_by=["sandbox.command.list", "sandbox.command.kill", "sandbox.pause"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SANDBOX_FILE_WRITE = CapabilitySchema(
    capability_key="sandbox.file.write",
    service="e2b",
    category="files",
    description="Write text or base64-decoded bytes into a sandbox file",
    parameters={
        "path": ParameterSchema(
            type="string",
            required=True,
            description="Destination path inside the sandbox",
        ),
        "content": ParameterSchema(
            type="string",
            required=True,
            description="Text payload or base64 string when encoding=base64",
        ),
        "encoding": ParameterSchema(
            type="string",
            required=False,
            description="Interpret content as text or base64",
            default="text",
            enum=["text", "base64"],
        ),
        "sandbox_id": ParameterSchema(
            type="string",
            required=False,
            description="Existing sandbox ID to reuse",
        ),
        "template": ParameterSchema(
            type="string",
            required=False,
            description="Template to use when a new sandbox is created",
        ),
        "timeout_seconds": ParameterSchema(
            type="integer",
            required=False,
            description="Sandbox lifetime if creating a new instance",
            default=3600,
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "path": ReturnFieldSchema(type="string", description="Written path"),
        "encoding": ReturnFieldSchema(type="string", description="Resolved encoding"),
        "size_bytes": ReturnFieldSchema(type="integer", description="Written byte size"),
        "status": ReturnFieldSchema(type="string", description="Should be 'written'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.ensure"],
        typically_followed_by=["sandbox.python.run", "sandbox.bash.run", "sandbox.file.read"],
    ),
    idempotent=True,
    has_side_effects=True,
)

SANDBOX_FILE_READ = CapabilitySchema(
    capability_key="sandbox.file.read",
    service="e2b",
    category="files",
    description="Read a sandbox file as text or base64",
    parameters={
        "path": ParameterSchema(
            type="string",
            required=True,
            description="Path inside the sandbox",
        ),
        "encoding": ParameterSchema(
            type="string",
            required=False,
            description="Return the file as text or base64",
            default="text",
            enum=["text", "base64"],
        ),
        "sandbox_id": ParameterSchema(
            type="string",
            required=False,
            description="Existing sandbox ID to reuse",
        ),
        "template": ParameterSchema(
            type="string",
            required=False,
            description="Template to use when a new sandbox is created",
        ),
        "timeout_seconds": ParameterSchema(
            type="integer",
            required=False,
            description="Sandbox lifetime if creating a new instance",
            default=3600,
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "path": ReturnFieldSchema(type="string", description="Read path"),
        "encoding": ReturnFieldSchema(type="string", description="Resolved encoding"),
        "content": ReturnFieldSchema(type="string", description="File payload"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File byte size"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.python.run", "sandbox.bash.run", "sandbox.file.write"],
        related_capabilities=["sandbox.file.write"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SANDBOX_PAUSE = CapabilitySchema(
    capability_key="sandbox.pause",
    service="e2b",
    category="sandbox",
    description="Pause a sandbox for later resume",
    parameters={
        "sandbox_id": ParameterSchema(
            type="string",
            required=True,
            description="Sandbox ID to pause",
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "status": ReturnFieldSchema(type="string", description="Should be 'paused'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.python.run", "sandbox.bash.run", "sandbox.file.read"],
        typically_followed_by=["sandbox.ensure", "sandbox.get_info"],
    ),
    idempotent=True,
    has_side_effects=True,
)

SANDBOX_TIMEOUT_SET = CapabilitySchema(
    capability_key="sandbox.timeout.set",
    service="e2b",
    category="sandbox",
    description="Update the timeout on an existing sandbox",
    parameters={
        "sandbox_id": ParameterSchema(
            type="string",
            required=True,
            description="Sandbox ID to update",
        ),
        "timeout_seconds": ParameterSchema(
            type="integer",
            required=True,
            description="New timeout in seconds",
            example=14400,
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "timeout_seconds": ReturnFieldSchema(type="integer", description="Updated timeout"),
        "status": ReturnFieldSchema(type="string", description="Should be 'updated'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.ensure", "sandbox.get_info"],
        typically_followed_by=["sandbox.pause", "sandbox.get_info"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SANDBOX_SNAPSHOT_CREATE = CapabilitySchema(
    capability_key="sandbox.snapshot.create",
    service="e2b",
    category="sandbox",
    description="Create a reusable snapshot of the current sandbox state",
    parameters={
        "sandbox_id": ParameterSchema(
            type="string",
            required=True,
            description="Sandbox ID to snapshot",
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "snapshot_id": ReturnFieldSchema(type="string", description="Created snapshot identifier"),
        "snapshot": ReturnFieldSchema(type="object", description="Raw snapshot metadata payload"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.python.run", "sandbox.bash.run", "sandbox.file.write"],
        typically_followed_by=["sandbox.pause", "sandbox.get_info"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SANDBOX_COMMAND_LIST = CapabilitySchema(
    capability_key="sandbox.command.list",
    service="e2b",
    category="execution",
    description="List running background commands in a sandbox",
    parameters={
        "sandbox_id": ParameterSchema(
            type="string",
            required=True,
            description="Sandbox ID to inspect",
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "processes": ReturnFieldSchema(type="array", description="Running process metadata"),
        "count": ReturnFieldSchema(type="integer", description="Number of active processes"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.python.run_background", "sandbox.bash.run_background"],
        related_capabilities=["sandbox.command.kill"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SANDBOX_COMMAND_KILL = CapabilitySchema(
    capability_key="sandbox.command.kill",
    service="e2b",
    category="execution",
    description="Terminate a background command in a sandbox",
    parameters={
        "sandbox_id": ParameterSchema(
            type="string",
            required=True,
            description="Sandbox ID containing the process",
        ),
        "pid": ParameterSchema(
            type="integer",
            required=True,
            description="Process ID returned by a background run",
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "pid": ReturnFieldSchema(type="integer", description="Process ID"),
        "killed": ReturnFieldSchema(type="boolean", description="Whether the process was found"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.command.list"],
        related_capabilities=["sandbox.command.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SANDBOX_GET_INFO = CapabilitySchema(
    capability_key="sandbox.get_info",
    service="e2b",
    category="sandbox",
    description="Inspect sandbox lifecycle and runtime metrics",
    parameters={
        "sandbox_id": ParameterSchema(
            type="string",
            required=True,
            description="Sandbox ID to inspect",
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "info": ReturnFieldSchema(type="object", description="Raw sandbox info payload"),
        "metrics": ReturnFieldSchema(type="object", description="Runtime metrics payload"),
        "timeout_seconds": ReturnFieldSchema(type="integer", description="Requested timeout"),
        "running": ReturnFieldSchema(type="boolean", description="Whether the sandbox is running"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.ensure", "sandbox.pause"],
        related_capabilities=["sandbox.pause"],
    ),
    idempotent=True,
    has_side_effects=False,
)

E2B_SCHEMAS = {
    "sandbox.ensure": SANDBOX_ENSURE,
    "sandbox.python.run": SANDBOX_PYTHON_RUN,
    "sandbox.python.run_background": SANDBOX_PYTHON_RUN_BACKGROUND,
    "sandbox.bash.run": SANDBOX_BASH_RUN,
    "sandbox.bash.run_background": SANDBOX_BASH_RUN_BACKGROUND,
    "sandbox.file.write": SANDBOX_FILE_WRITE,
    "sandbox.file.read": SANDBOX_FILE_READ,
    "sandbox.command.list": SANDBOX_COMMAND_LIST,
    "sandbox.command.kill": SANDBOX_COMMAND_KILL,
    "sandbox.pause": SANDBOX_PAUSE,
    "sandbox.timeout.set": SANDBOX_TIMEOUT_SET,
    "sandbox.snapshot.create": SANDBOX_SNAPSHOT_CREATE,
    "sandbox.get_info": SANDBOX_GET_INFO,
}

__all__ = ["E2B_SCHEMAS"]
