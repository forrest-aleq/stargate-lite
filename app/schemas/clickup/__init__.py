"""
ClickUp Capability Schemas.

Rich metadata for ClickUp task, list, space, and workspace operations.
Finance teams use ClickUp for approval workflows, month-end checklists, and project tracking.
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

CLICKUP_TASK_CREATE = CapabilitySchema(
    capability_key="clickup.task.create",
    service="clickup",
    category="tasks",
    description="Create task in ClickUp for finance workflows (approvals, reviews, month-end)",
    description_detailed=(
        "Create a new task in a ClickUp list. Supports assignees, priorities, "
        "due dates, and status. Ideal for invoice approvals, audit items, and close tasks."
    ),
    parameters={
        "list_id": ParameterSchema(
            type="string",
            required=True,
            description="ID of the list to create task in",
            example="901234567",
        ),
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Task name",
            example="Review January invoices",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Task description (supports markdown)",
        ),
        "assignees": ParameterSchema(
            type="array",
            required=False,
            description="List of user IDs to assign",
            items_type="integer",
        ),
        "priority": ParameterSchema(
            type="integer",
            required=False,
            description="Priority level",
            enum=["1", "2", "3", "4"],
        ),
        "due_date": ParameterSchema(
            type="integer",
            required=False,
            description="Due date timestamp (milliseconds)",
        ),
        "start_date": ParameterSchema(
            type="integer",
            required=False,
            description="Start date timestamp (milliseconds)",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Status name (must match list's statuses)",
            example="in progress",
        ),
        "tags": ParameterSchema(
            type="array",
            required=False,
            description="List of tag names",
            items_type="string",
        ),
    },
    returns={
        "task_id": ReturnFieldSchema(type="string", description="Created task ID"),
        "name": ReturnFieldSchema(type="string", description="Task name"),
        "url": ReturnFieldSchema(type="string", description="Direct link to task"),
        "status": ReturnFieldSchema(type="string", description="Task status"),
        "assignees": ReturnFieldSchema(type="array", description="Assigned usernames"),
        "due_date": ReturnFieldSchema(type="string", description="Due date timestamp"),
        "priority": ReturnFieldSchema(type="integer", description="Priority level"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="list_id or name missing",
            recovery_hint="Provide both list_id and task name",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.list.get", "clickup.list.get_in_folder"],
        typically_followed_by=["clickup.comment.create", "clickup.task.update"],
        related_capabilities=["clickup.task.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ TASK GET ============

CLICKUP_TASK_GET = CapabilitySchema(
    capability_key="clickup.task.get",
    service="clickup",
    category="tasks",
    description="Get task details from ClickUp",
    description_detailed=(
        "Retrieve full details of a specific task including description, "
        "assignees, tags, dates, and custom fields. Optionally include subtasks."
    ),
    parameters={
        "task_id": ParameterSchema(
            type="string",
            required=True,
            description="Task ID to retrieve",
            example="abc123def",
        ),
        "include_subtasks": ParameterSchema(
            type="boolean",
            required=False,
            description="Include subtasks in response (default: false)",
        ),
    },
    returns={
        "task_id": ReturnFieldSchema(type="string", description="Task ID"),
        "name": ReturnFieldSchema(type="string", description="Task name"),
        "description": ReturnFieldSchema(type="string", description="Task description"),
        "status": ReturnFieldSchema(type="string", description="Current status"),
        "assignees": ReturnFieldSchema(
            type="array",
            description="Assignees with id, username, email",
        ),
        "due_date": ReturnFieldSchema(type="string", description="Due date timestamp"),
        "start_date": ReturnFieldSchema(type="string", description="Start date timestamp"),
        "priority": ReturnFieldSchema(type="integer", description="Priority level"),
        "tags": ReturnFieldSchema(type="array", description="Tag names"),
        "url": ReturnFieldSchema(type="string", description="Direct link to task"),
        "date_created": ReturnFieldSchema(type="string", description="Creation timestamp"),
        "date_updated": ReturnFieldSchema(type="string", description="Last update timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Task not found",
            recovery_hint="Verify task_id exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.task.list", "clickup.task.create"],
        typically_followed_by=["clickup.task.update", "clickup.comment.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ TASK UPDATE ============

CLICKUP_TASK_UPDATE = CapabilitySchema(
    capability_key="clickup.task.update",
    service="clickup",
    category="tasks",
    description="Update task in ClickUp (status, assignees, priority)",
    description_detailed=(
        "Update an existing task's properties. Only provided fields are updated. "
        "Use for changing status, reassigning, or updating due dates."
    ),
    parameters={
        "task_id": ParameterSchema(
            type="string",
            required=True,
            description="Task ID to update",
            example="abc123def",
        ),
        "name": ParameterSchema(
            type="string",
            required=False,
            description="New task name",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="New description",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="New status name",
            example="complete",
        ),
        "priority": ParameterSchema(
            type="integer",
            required=False,
            description="New priority (1=urgent, 4=low)",
            enum=["1", "2", "3", "4"],
        ),
        "assignees": ParameterSchema(
            type="array",
            required=False,
            description="New assignee IDs (replaces existing)",
            items_type="integer",
        ),
        "due_date": ParameterSchema(
            type="integer",
            required=False,
            description="New due date timestamp (milliseconds)",
        ),
        "start_date": ParameterSchema(
            type="integer",
            required=False,
            description="New start date timestamp (milliseconds)",
        ),
    },
    returns={
        "task_id": ReturnFieldSchema(type="string", description="Updated task ID"),
        "name": ReturnFieldSchema(type="string", description="Task name"),
        "status": ReturnFieldSchema(type="string", description="New status"),
        "url": ReturnFieldSchema(type="string", description="Direct link to task"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Task not found or invalid status",
            recovery_hint="Verify task_id exists and status matches list configuration",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.task.get"],
        related_capabilities=["clickup.comment.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ TASK LIST ============

CLICKUP_TASK_LIST = CapabilitySchema(
    capability_key="clickup.task.list",
    service="clickup",
    category="tasks",
    description="List tasks in ClickUp with filtering",
    description_detailed=(
        "List tasks in a list with optional filtering by status, assignees, "
        "tags, and due dates. Supports pagination (max 100 per page)."
    ),
    parameters={
        "list_id": ParameterSchema(
            type="string",
            required=True,
            description="List ID to get tasks from",
            example="901234567",
        ),
        "archived": ParameterSchema(
            type="boolean",
            required=False,
            description="Include archived tasks (default: false)",
        ),
        "page": ParameterSchema(
            type="integer",
            required=False,
            description="Page number (0-indexed)",
        ),
        "order_by": ParameterSchema(
            type="string",
            required=False,
            description="Sort field",
            enum=["created", "updated", "due_date"],
        ),
        "reverse": ParameterSchema(
            type="boolean",
            required=False,
            description="Reverse sort order (default: false)",
        ),
        "subtasks": ParameterSchema(
            type="boolean",
            required=False,
            description="Include subtasks (default: false)",
        ),
        "statuses": ParameterSchema(
            type="array",
            required=False,
            description="Filter by status names",
            items_type="string",
        ),
        "assignees": ParameterSchema(
            type="array",
            required=False,
            description="Filter by assignee IDs",
            items_type="integer",
        ),
        "tags": ParameterSchema(
            type="array",
            required=False,
            description="Filter by tag names",
            items_type="string",
        ),
        "due_date_gt": ParameterSchema(
            type="integer",
            required=False,
            description="Due date greater than (timestamp)",
        ),
        "due_date_lt": ParameterSchema(
            type="integer",
            required=False,
            description="Due date less than (timestamp)",
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of tasks returned"),
        "tasks": ReturnFieldSchema(
            type="array",
            description="Tasks with task_id, name, status, assignees, due_date, priority, url",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="List not found",
            recovery_hint="Verify list_id exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.list.get", "clickup.list.get_in_folder"],
        typically_followed_by=["clickup.task.get", "clickup.task.update"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ LIST GET ============

CLICKUP_LIST_GET = CapabilitySchema(
    capability_key="clickup.list.get",
    service="clickup",
    category="lists",
    description="Get list details from ClickUp",
    description_detailed=(
        "Get details of a specific list including statuses, folder, space, "
        "and task count. Essential for understanding list structure."
    ),
    parameters={
        "list_id": ParameterSchema(
            type="string",
            required=True,
            description="List ID to retrieve",
            example="901234567",
        ),
    },
    returns={
        "list_id": ReturnFieldSchema(type="string", description="List ID"),
        "name": ReturnFieldSchema(type="string", description="List name"),
        "folder": ReturnFieldSchema(type="object", description="Parent folder with id, name"),
        "space": ReturnFieldSchema(type="object", description="Parent space with id, name"),
        "statuses": ReturnFieldSchema(
            type="array",
            description="Available statuses with status, type, color",
        ),
        "task_count": ReturnFieldSchema(type="integer", description="Number of tasks"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="List not found",
            recovery_hint="Verify list_id exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.list.get_in_folder", "clickup.list.get_in_space"],
        typically_followed_by=["clickup.task.list", "clickup.task.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ LIST GET IN FOLDER ============

CLICKUP_LIST_GET_IN_FOLDER = CapabilitySchema(
    capability_key="clickup.list.get_in_folder",
    service="clickup",
    category="lists",
    description="Get all lists in a ClickUp folder",
    description_detailed=(
        "Retrieve all lists within a specific folder. Optionally include archived lists."
    ),
    parameters={
        "folder_id": ParameterSchema(
            type="string",
            required=True,
            description="Folder ID to get lists from",
            example="456789012",
        ),
        "archived": ParameterSchema(
            type="boolean",
            required=False,
            description="Include archived lists (default: false)",
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of lists"),
        "lists": ReturnFieldSchema(
            type="array",
            description="Lists with list_id, name, task_count",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Folder not found",
            recovery_hint="Verify folder_id exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.space.get"],
        typically_followed_by=["clickup.list.get", "clickup.task.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ LIST GET IN SPACE ============

CLICKUP_LIST_GET_IN_SPACE = CapabilitySchema(
    capability_key="clickup.list.get_in_space",
    service="clickup",
    category="lists",
    description="Get folderless lists in a ClickUp space",
    description_detailed=(
        "Retrieve lists that are directly in a space (not in any folder). "
        "Optionally include archived lists."
    ),
    parameters={
        "space_id": ParameterSchema(
            type="string",
            required=True,
            description="Space ID to get lists from",
            example="789012345",
        ),
        "archived": ParameterSchema(
            type="boolean",
            required=False,
            description="Include archived lists (default: false)",
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of lists"),
        "lists": ReturnFieldSchema(
            type="array",
            description="Lists with list_id, name, task_count",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Space not found",
            recovery_hint="Verify space_id exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.space.list", "clickup.space.get"],
        typically_followed_by=["clickup.list.get", "clickup.task.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ SPACE LIST ============

CLICKUP_SPACE_LIST = CapabilitySchema(
    capability_key="clickup.space.list",
    service="clickup",
    category="spaces",
    description="List spaces in ClickUp workspace",
    description_detailed=(
        "Get all spaces in a workspace (team). Optionally include archived spaces."
    ),
    parameters={
        "team_id": ParameterSchema(
            type="string",
            required=True,
            description="Team/Workspace ID",
            example="123456789",
        ),
        "archived": ParameterSchema(
            type="boolean",
            required=False,
            description="Include archived spaces (default: false)",
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of spaces"),
        "spaces": ReturnFieldSchema(
            type="array",
            description="Spaces with space_id, name, private, statuses",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Team not found",
            recovery_hint="Verify team_id exists using clickup.team.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.team.list"],
        typically_followed_by=["clickup.space.get", "clickup.list.get_in_space"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ SPACE GET ============

CLICKUP_SPACE_GET = CapabilitySchema(
    capability_key="clickup.space.get",
    service="clickup",
    category="spaces",
    description="Get space details from ClickUp",
    description_detailed=("Get full details of a specific space including statuses and features."),
    parameters={
        "space_id": ParameterSchema(
            type="string",
            required=True,
            description="Space ID to retrieve",
            example="789012345",
        ),
    },
    returns={
        "space_id": ReturnFieldSchema(type="string", description="Space ID"),
        "name": ReturnFieldSchema(type="string", description="Space name"),
        "private": ReturnFieldSchema(type="boolean", description="Is private space"),
        "statuses": ReturnFieldSchema(
            type="array",
            description="Available statuses with status, type, color",
        ),
        "features": ReturnFieldSchema(type="object", description="Enabled features"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Space not found",
            recovery_hint="Verify space_id exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.space.list"],
        typically_followed_by=["clickup.list.get_in_space", "clickup.list.get_in_folder"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ COMMENT CREATE ============

CLICKUP_COMMENT_CREATE = CapabilitySchema(
    capability_key="clickup.comment.create",
    service="clickup",
    category="comments",
    description="Create comment on ClickUp task",
    description_detailed=(
        "Post a comment on a task. Optionally assign with the comment " "and notify all assignees."
    ),
    parameters={
        "task_id": ParameterSchema(
            type="string",
            required=True,
            description="Task ID to comment on",
            example="abc123def",
        ),
        "comment_text": ParameterSchema(
            type="string",
            required=True,
            description="Comment text",
            example="Approved by finance team.",
        ),
        "assignee": ParameterSchema(
            type="integer",
            required=False,
            description="User ID to assign with this comment",
        ),
        "notify_all": ParameterSchema(
            type="boolean",
            required=False,
            description="Notify all assignees (default: false)",
        ),
    },
    returns={
        "comment_id": ReturnFieldSchema(type="string", description="Created comment ID"),
        "hist_id": ReturnFieldSchema(type="string", description="History ID"),
        "date": ReturnFieldSchema(type="string", description="Creation timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Task not found or empty comment",
            recovery_hint="Verify task_id exists and comment_text is not empty",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.task.get", "clickup.task.update"],
        typically_followed_by=["clickup.comment.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ COMMENT LIST ============

CLICKUP_COMMENT_LIST = CapabilitySchema(
    capability_key="clickup.comment.list",
    service="clickup",
    category="comments",
    description="Get all comments on ClickUp task",
    description_detailed=(
        "Retrieve all comments on a specific task. Useful for viewing "
        "approval history and team discussions."
    ),
    parameters={
        "task_id": ParameterSchema(
            type="string",
            required=True,
            description="Task ID to get comments for",
            example="abc123def",
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of comments"),
        "comments": ReturnFieldSchema(
            type="array",
            description="Comments with comment_id, comment_text, user, date",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Task not found",
            recovery_hint="Verify task_id exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["clickup.task.get", "clickup.comment.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ TEAM LIST ============

CLICKUP_TEAM_LIST = CapabilitySchema(
    capability_key="clickup.team.list",
    service="clickup",
    category="teams",
    description="Get all ClickUp workspaces user has access to",
    description_detailed=(
        "List all workspaces (teams) the authenticated user has access to. "
        "This is the starting point for navigating the ClickUp hierarchy."
    ),
    parameters={},
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of teams"),
        "teams": ReturnFieldSchema(
            type="array",
            description="Teams with team_id, name, color, avatar",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="ClickUp OAuth token not configured",
            recovery_hint="User must connect ClickUp workspace to Aleq",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["clickup.space.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# Export all schemas
CLICKUP_SCHEMAS: dict[str, CapabilitySchema] = {
    "clickup.task.create": CLICKUP_TASK_CREATE,
    "clickup.task.get": CLICKUP_TASK_GET,
    "clickup.task.update": CLICKUP_TASK_UPDATE,
    "clickup.task.list": CLICKUP_TASK_LIST,
    "clickup.list.get": CLICKUP_LIST_GET,
    "clickup.list.get_in_folder": CLICKUP_LIST_GET_IN_FOLDER,
    "clickup.list.get_in_space": CLICKUP_LIST_GET_IN_SPACE,
    "clickup.space.list": CLICKUP_SPACE_LIST,
    "clickup.space.get": CLICKUP_SPACE_GET,
    "clickup.comment.create": CLICKUP_COMMENT_CREATE,
    "clickup.comment.list": CLICKUP_COMMENT_LIST,
    "clickup.team.list": CLICKUP_TEAM_LIST,
}

__all__ = ["CLICKUP_SCHEMAS"]
