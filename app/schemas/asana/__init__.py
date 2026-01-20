"""
Asana Capability Schemas.

Rich metadata for Asana task, project, section, and custom field operations.
Finance teams use Asana for project tracking, workflow management, and team coordination.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ TASK CREATE ============

ASANA_TASK_CREATE = CapabilitySchema(
    capability_key="asana.task.create",
    service="asana",
    category="tasks",
    description="Create task in Asana",
    description_detailed=(
        "Create a new task in Asana. Can be added to one or more projects, "
        "assigned to a user, and include custom fields. Supports subtasks via parent field."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "task_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the task",
            example="Review Q4 financials",
        ),
        "workspace_gid": ParameterSchema(
            type="string",
            required=True,
            description="Workspace GID",
            example="1234567890123456",
        ),
        "projects": ParameterSchema(
            type="array",
            required=False,
            description="Array of project GIDs to add task to",
            items_type="string",
        ),
        "notes": ParameterSchema(
            type="string",
            required=False,
            description="Task description/notes",
        ),
        "assignee": ParameterSchema(
            type="string",
            required=False,
            description="User GID to assign task to",
        ),
        "due_on": ParameterSchema(
            type="string",
            required=False,
            description="Due date (YYYY-MM-DD)",
            example="2025-01-31",
        ),
        "due_at": ParameterSchema(
            type="string",
            required=False,
            description="Due datetime (ISO 8601)",
        ),
        "custom_fields": ParameterSchema(
            type="object",
            required=False,
            description="Custom field values as {field_gid: value}",
        ),
        "parent": ParameterSchema(
            type="string",
            required=False,
            description="Parent task GID (for creating subtasks)",
        ),
    },
    returns={
        "task_gid": ReturnFieldSchema(type="string", description="Created task GID"),
        "name": ReturnFieldSchema(type="string", description="Task name"),
        "permalink_url": ReturnFieldSchema(type="string", description="Direct link to task"),
        "created_at": ReturnFieldSchema(type="string", description="Creation timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Missing required fields",
            recovery_hint="Provide task_name and workspace_gid",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.project.list", "asana.project.get"],
        typically_followed_by=["asana.section.addtask", "asana.customfield.update"],
        related_capabilities=["asana.task.update"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ TASK UPDATE ============

ASANA_TASK_UPDATE = CapabilitySchema(
    capability_key="asana.task.update",
    service="asana",
    category="tasks",
    description="Update existing task",
    description_detailed=(
        "Update an existing task's properties. Only provided fields are updated. "
        "Can mark tasks complete, reassign, or update custom fields."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "task_gid": ParameterSchema(
            type="string",
            required=True,
            description="Task GID to update",
            example="1234567890123456",
        ),
        "name": ParameterSchema(
            type="string",
            required=False,
            description="New task name",
        ),
        "notes": ParameterSchema(
            type="string",
            required=False,
            description="New description/notes",
        ),
        "completed": ParameterSchema(
            type="boolean",
            required=False,
            description="Mark task as complete/incomplete",
        ),
        "assignee": ParameterSchema(
            type="string",
            required=False,
            description="New assignee GID (null to unassign)",
        ),
        "due_on": ParameterSchema(
            type="string",
            required=False,
            description="New due date (YYYY-MM-DD, null to clear)",
        ),
        "custom_fields": ParameterSchema(
            type="object",
            required=False,
            description="Custom field values to update",
        ),
    },
    returns={
        "task_gid": ReturnFieldSchema(type="string", description="Updated task GID"),
        "name": ReturnFieldSchema(type="string", description="Task name"),
        "completed": ReturnFieldSchema(type="boolean", description="Completion status"),
        "modified_at": ReturnFieldSchema(type="string", description="Last modification timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Task not found",
            recovery_hint="Verify task_gid exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.task.get"],
        related_capabilities=["asana.customfield.update"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ TASK GET ============

ASANA_TASK_GET = CapabilitySchema(
    capability_key="asana.task.get",
    service="asana",
    category="tasks",
    description="Get task details",
    description_detailed=(
        "Retrieve full details of a specific task including custom fields, "
        "projects, tags, and assignee information."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "task_gid": ParameterSchema(
            type="string",
            required=True,
            description="Task GID to retrieve",
            example="1234567890123456",
        ),
        "opt_fields": ParameterSchema(
            type="string",
            required=False,
            description="Comma-separated fields to include",
        ),
    },
    returns={
        "task_gid": ReturnFieldSchema(type="string", description="Task GID"),
        "name": ReturnFieldSchema(type="string", description="Task name"),
        "notes": ReturnFieldSchema(type="string", description="Task description"),
        "completed": ReturnFieldSchema(type="boolean", description="Completion status"),
        "assignee": ReturnFieldSchema(type="object", description="Assignee details"),
        "due_on": ReturnFieldSchema(type="string", description="Due date"),
        "custom_fields": ReturnFieldSchema(type="array", description="Custom field values"),
        "projects": ReturnFieldSchema(type="array", description="Projects task belongs to"),
        "tags": ReturnFieldSchema(type="array", description="Task tags"),
        "permalink_url": ReturnFieldSchema(type="string", description="Direct link to task"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Task not found",
            recovery_hint="Verify task_gid exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.task.list", "asana.task.create"],
        typically_followed_by=["asana.task.update", "asana.customfield.update"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ TASK LIST ============

ASANA_TASK_LIST = CapabilitySchema(
    capability_key="asana.task.list",
    service="asana",
    category="tasks",
    description="List tasks in project",
    description_detailed=(
        "List all tasks in a specific project. Returns tasks with basic "
        "information including completion status and assignee."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "project_gid": ParameterSchema(
            type="string",
            required=True,
            description="Project GID to list tasks from",
            example="1234567890123456",
        ),
        "opt_fields": ParameterSchema(
            type="string",
            required=False,
            description="Comma-separated fields to include (default: name,completed,assignee,due_on)",  # noqa: E501
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max tasks to return (default: 100)",
        ),
    },
    returns={
        "tasks": ReturnFieldSchema(
            type="array",
            description="Tasks with task_gid, name, completed, assignee, due_on",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Project not found",
            recovery_hint="Verify project_gid exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.project.list", "asana.project.get"],
        typically_followed_by=["asana.task.get", "asana.task.update"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ PROJECT CREATE ============

ASANA_PROJECT_CREATE = CapabilitySchema(
    capability_key="asana.project.create",
    service="asana",
    category="projects",
    description="Create project in Asana",
    description_detailed=(
        "Create a new project in Asana. Can be a list or board layout. "
        "Optionally assign to a team and set owner."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "project_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the project",
            example="Q1 2025 Close",
        ),
        "workspace_gid": ParameterSchema(
            type="string",
            required=True,
            description="Workspace GID",
        ),
        "notes": ParameterSchema(
            type="string",
            required=False,
            description="Project description",
        ),
        "layout": ParameterSchema(
            type="string",
            required=False,
            description="Project layout (default: list)",
            enum=["list", "board"],
        ),
        "team": ParameterSchema(
            type="string",
            required=False,
            description="Team GID to assign project to",
        ),
        "color": ParameterSchema(
            type="string",
            required=False,
            description="Project color",
        ),
        "owner": ParameterSchema(
            type="string",
            required=False,
            description="Owner user GID",
        ),
        "due_date": ParameterSchema(
            type="string",
            required=False,
            description="Project due date (YYYY-MM-DD)",
        ),
    },
    returns={
        "project_gid": ReturnFieldSchema(type="string", description="Created project GID"),
        "name": ReturnFieldSchema(type="string", description="Project name"),
        "permalink_url": ReturnFieldSchema(type="string", description="Direct link to project"),
        "created_at": ReturnFieldSchema(type="string", description="Creation timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Missing required fields",
            recovery_hint="Provide project_name and workspace_gid",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["asana.section.create", "asana.task.create"],
        related_capabilities=["asana.customfield.add"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ PROJECT GET ============

ASANA_PROJECT_GET = CapabilitySchema(
    capability_key="asana.project.get",
    service="asana",
    category="projects",
    description="Get project details",
    description_detailed=(
        "Retrieve full details of a specific project including members, "
        "custom fields, owner, and team information."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "project_gid": ParameterSchema(
            type="string",
            required=True,
            description="Project GID to retrieve",
            example="1234567890123456",
        ),
        "opt_fields": ParameterSchema(
            type="string",
            required=False,
            description="Comma-separated fields to include",
        ),
    },
    returns={
        "project_gid": ReturnFieldSchema(type="string", description="Project GID"),
        "name": ReturnFieldSchema(type="string", description="Project name"),
        "notes": ReturnFieldSchema(type="string", description="Project description"),
        "color": ReturnFieldSchema(type="string", description="Project color"),
        "completed": ReturnFieldSchema(type="boolean", description="Completion status"),
        "owner": ReturnFieldSchema(type="object", description="Owner details"),
        "team": ReturnFieldSchema(type="object", description="Team details"),
        "members": ReturnFieldSchema(type="array", description="Project members"),
        "custom_fields": ReturnFieldSchema(type="array", description="Custom field settings"),
        "permalink_url": ReturnFieldSchema(type="string", description="Direct link to project"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Project not found",
            recovery_hint="Verify project_gid exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.project.list"],
        typically_followed_by=["asana.task.list", "asana.section.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ PROJECT LIST ============

ASANA_PROJECT_LIST = CapabilitySchema(
    capability_key="asana.project.list",
    service="asana",
    category="projects",
    description="List projects in workspace",
    description_detailed=(
        "List all projects in a workspace. Returns projects with basic "
        "information including owner and completion status."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "workspace_gid": ParameterSchema(
            type="string",
            required=True,
            description="Workspace GID to list projects from",
            example="1234567890123456",
        ),
        "opt_fields": ParameterSchema(
            type="string",
            required=False,
            description="Comma-separated fields to include (default: name,owner,completed)",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max projects to return (default: 100)",
        ),
    },
    returns={
        "projects": ReturnFieldSchema(
            type="array",
            description="Projects with project_gid, name, owner, completed",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["asana.project.get", "asana.task.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ CUSTOM FIELD ADD ============

ASANA_CUSTOMFIELD_ADD = CapabilitySchema(
    capability_key="asana.customfield.add",
    service="asana",
    category="custom_fields",
    description="Add custom field to project",
    description_detailed=(
        "Add an existing custom field to a project. Custom fields must be "
        "created in Asana first, then can be added to multiple projects."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "project_gid": ParameterSchema(
            type="string",
            required=True,
            description="Project GID to add field to",
            example="1234567890123456",
        ),
        "custom_field_gid": ParameterSchema(
            type="string",
            required=True,
            description="Custom field GID to add",
        ),
        "insert_before": ParameterSchema(
            type="string",
            required=False,
            description="Field GID to insert before (for ordering)",
        ),
        "insert_after": ParameterSchema(
            type="string",
            required=False,
            description="Field GID to insert after (for ordering)",
        ),
    },
    returns={
        "custom_field_setting_gid": ReturnFieldSchema(
            type="string",
            description="Custom field setting GID",
        ),
        "custom_field": ReturnFieldSchema(type="object", description="Custom field details"),
        "project": ReturnFieldSchema(type="object", description="Project details"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Custom field or project not found",
            recovery_hint="Verify both GIDs exist",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.project.create"],
        typically_followed_by=["asana.customfield.update"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ CUSTOM FIELD UPDATE ============

ASANA_CUSTOMFIELD_UPDATE = CapabilitySchema(
    capability_key="asana.customfield.update",
    service="asana",
    category="custom_fields",
    description="Update custom field on task",
    description_detailed=(
        "Update the value of a custom field on a task. The value format "
        "depends on the field type (text, number, enum, etc.)."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "task_gid": ParameterSchema(
            type="string",
            required=True,
            description="Task GID to update",
            example="1234567890123456",
        ),
        "custom_field_gid": ParameterSchema(
            type="string",
            required=True,
            description="Custom field GID",
        ),
        "value": ParameterSchema(
            type="object",
            required=True,
            description="New value (type depends on field type - can be string, number, or object)",
        ),
    },
    returns={
        "task_gid": ReturnFieldSchema(type="string", description="Updated task GID"),
        "custom_fields": ReturnFieldSchema(type="array", description="Updated custom fields"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid value for field type",
            recovery_hint="Check custom field type and provide compatible value",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.task.get"],
        related_capabilities=["asana.task.update"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ SECTION CREATE ============

ASANA_SECTION_CREATE = CapabilitySchema(
    capability_key="asana.section.create",
    service="asana",
    category="sections",
    description="Create section in project",
    description_detailed=(
        "Create a new section in a project. Sections help organize tasks "
        "into groups like 'To Do', 'In Progress', 'Complete'."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "project_gid": ParameterSchema(
            type="string",
            required=True,
            description="Project GID to create section in",
            example="1234567890123456",
        ),
        "section_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the section",
            example="In Review",
        ),
        "insert_before": ParameterSchema(
            type="string",
            required=False,
            description="Section GID to insert before (for ordering)",
        ),
        "insert_after": ParameterSchema(
            type="string",
            required=False,
            description="Section GID to insert after (for ordering)",
        ),
    },
    returns={
        "section_gid": ReturnFieldSchema(type="string", description="Created section GID"),
        "name": ReturnFieldSchema(type="string", description="Section name"),
        "project": ReturnFieldSchema(type="object", description="Parent project details"),
        "created_at": ReturnFieldSchema(type="string", description="Creation timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Project not found",
            recovery_hint="Verify project_gid exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.project.create", "asana.project.get"],
        typically_followed_by=["asana.section.addtask", "asana.task.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ SECTION ADD TASK ============

ASANA_SECTION_ADDTASK = CapabilitySchema(
    capability_key="asana.section.addtask",
    service="asana",
    category="sections",
    description="Add task to section",
    description_detailed=(
        "Move a task into a section within a project. Can optionally specify "
        "position within the section."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "section_gid": ParameterSchema(
            type="string",
            required=True,
            description="Section GID to add task to",
            example="1234567890123456",
        ),
        "task_gid": ParameterSchema(
            type="string",
            required=True,
            description="Task GID to move",
        ),
        "insert_before": ParameterSchema(
            type="string",
            required=False,
            description="Task GID to insert before (for ordering)",
        ),
        "insert_after": ParameterSchema(
            type="string",
            required=False,
            description="Task GID to insert after (for ordering)",
        ),
    },
    returns={
        "success": ReturnFieldSchema(type="boolean", description="Operation success"),
        "section_gid": ReturnFieldSchema(type="string", description="Section GID"),
        "task_gid": ReturnFieldSchema(type="string", description="Task GID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Section or task not found",
            recovery_hint="Verify both GIDs exist",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.task.create", "asana.section.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ ATTACHMENT UPLOAD ============

ASANA_ATTACHMENT_UPLOAD = CapabilitySchema(
    capability_key="asana.attachment.upload",
    service="asana",
    category="attachments",
    description="Upload attachment to task",
    description_detailed=(
        "Upload a file attachment to a task. Useful for attaching invoices, "
        "receipts, or documentation."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Asana OAuth access token",
        ),
        "task_gid": ParameterSchema(
            type="string",
            required=True,
            description="Task GID to attach file to",
            example="1234567890123456",
        ),
        "file_content": ParameterSchema(
            type="string",
            required=True,
            description="File content (base64 encoded or binary stream)",
        ),
        "file_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the uploaded file",
            example="invoice-2025-01.pdf",
        ),
    },
    returns={
        "attachment_gid": ReturnFieldSchema(type="string", description="Uploaded attachment GID"),
        "name": ReturnFieldSchema(type="string", description="Attachment name"),
        "download_url": ReturnFieldSchema(type="string", description="Download URL (temporary)"),
        "permanent_url": ReturnFieldSchema(type="string", description="Permanent Asana URL"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Asana access token not provided",
            recovery_hint="User must grant Aleq access to Asana workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Task not found or invalid file",
            recovery_hint="Verify task_gid exists and file content is valid",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["asana.task.create", "asana.task.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# Export all schemas
ASANA_SCHEMAS: dict[str, CapabilitySchema] = {
    "asana.task.create": ASANA_TASK_CREATE,
    "asana.task.update": ASANA_TASK_UPDATE,
    "asana.task.get": ASANA_TASK_GET,
    "asana.task.list": ASANA_TASK_LIST,
    "asana.project.create": ASANA_PROJECT_CREATE,
    "asana.project.get": ASANA_PROJECT_GET,
    "asana.project.list": ASANA_PROJECT_LIST,
    "asana.customfield.add": ASANA_CUSTOMFIELD_ADD,
    "asana.customfield.update": ASANA_CUSTOMFIELD_UPDATE,
    "asana.section.create": ASANA_SECTION_CREATE,
    "asana.section.addtask": ASANA_SECTION_ADDTASK,
    "asana.attachment.upload": ASANA_ATTACHMENT_UPLOAD,
}

__all__ = ["ASANA_SCHEMAS"]
