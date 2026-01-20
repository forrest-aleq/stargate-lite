"""
Monday.com Capability Schemas.

Rich metadata for Monday.com board, item, column, and workflow operations.
Finance teams use Monday.com for invoice approval, month-end tracking, and project coordination.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ BOARD LIST ============

MONDAY_BOARD_LIST = CapabilitySchema(
    capability_key="monday.board.list",
    service="monday",
    category="boards",
    description="List boards in Monday.com workspace",
    description_detailed=(
        "Get all boards accessible to the authenticated user. "
        "Supports filtering by board kind (public/private) and state (active/archived)."
    ),
    parameters={
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of boards to return (default: 25)",
            example=50,
        ),
        "board_kind": ParameterSchema(
            type="string",
            required=False,
            description="Filter by board kind",
            enum=["public", "private", "share"],
        ),
        "state": ParameterSchema(
            type="string",
            required=False,
            description="Filter by state",
            enum=["active", "archived", "deleted", "all"],
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of boards returned"),
        "boards": ReturnFieldSchema(
            type="array",
            description="List of boards with id, name, description, state, item_count, owner",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["monday.board.get", "monday.item.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ BOARD GET ============

MONDAY_BOARD_GET = CapabilitySchema(
    capability_key="monday.board.get",
    service="monday",
    category="boards",
    description="Get board details from Monday.com with columns and groups",
    description_detailed=(
        "Get full details of a specific board including all columns (fields), "
        "groups (sections), and owner information. Essential for understanding "
        "board structure before creating or updating items."
    ),
    parameters={
        "board_id": ParameterSchema(
            type="string",
            required=True,
            description="Board ID to retrieve",
            example="1234567890",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Board ID"),
        "name": ReturnFieldSchema(type="string", description="Board name"),
        "description": ReturnFieldSchema(type="string", description="Board description"),
        "state": ReturnFieldSchema(type="string", description="Board state"),
        "board_kind": ReturnFieldSchema(type="string", description="public/private/share"),
        "item_count": ReturnFieldSchema(type="integer", description="Number of items"),
        "columns": ReturnFieldSchema(
            type="array",
            description="Column definitions with id, title, type, settings",
        ),
        "groups": ReturnFieldSchema(
            type="array",
            description="Group definitions with id, title, color",
        ),
        "owner": ReturnFieldSchema(type="object", description="Board owner details"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Board not found",
            recovery_hint="Verify board_id exists and user has access",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.board.list"],
        typically_followed_by=["monday.item.create", "monday.item.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ ITEM CREATE ============

MONDAY_ITEM_CREATE = CapabilitySchema(
    capability_key="monday.item.create",
    service="monday",
    category="items",
    description="Create item on Monday.com board for finance workflows",
    description_detailed=(
        "Create a new item (row) on a Monday.com board. Optionally specify "
        "a group and initial column values. Use for invoice tracking, "
        "approval workflows, and month-end close tasks."
    ),
    parameters={
        "board_id": ParameterSchema(
            type="string",
            required=True,
            description="Board ID to create item on",
            example="1234567890",
        ),
        "item_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the new item",
            example="Review Q4 expenses",
        ),
        "group_id": ParameterSchema(
            type="string",
            required=False,
            description="Group ID to add item to (defaults to first group)",
            example="topics",
        ),
        "column_values": ParameterSchema(
            type="object",
            required=False,
            description='JSON object of column values (e.g., {"status": {"label": "Done"}})',
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Created item ID"),
        "name": ReturnFieldSchema(type="string", description="Item name"),
        "url": ReturnFieldSchema(type="string", description="Relative link to item"),
        "state": ReturnFieldSchema(type="string", description="Item state"),
        "created_at": ReturnFieldSchema(type="string", description="Creation timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="board_id or item_name missing",
            recovery_hint="Provide both board_id and item_name",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.board.get"],
        typically_followed_by=["monday.column.change_value", "monday.update.create"],
        related_capabilities=["monday.item.update"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ ITEM GET ============

MONDAY_ITEM_GET = CapabilitySchema(
    capability_key="monday.item.get",
    service="monday",
    category="items",
    description="Get item details from Monday.com",
    description_detailed=(
        "Retrieve full details of a specific item including all column values, "
        "creator, board, and group information."
    ),
    parameters={
        "item_id": ParameterSchema(
            type="string",
            required=True,
            description="Item ID to retrieve",
            example="9876543210",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Item ID"),
        "name": ReturnFieldSchema(type="string", description="Item name"),
        "state": ReturnFieldSchema(type="string", description="Item state"),
        "url": ReturnFieldSchema(type="string", description="Relative link to item"),
        "created_at": ReturnFieldSchema(type="string", description="Creation timestamp"),
        "updated_at": ReturnFieldSchema(type="string", description="Last update timestamp"),
        "creator": ReturnFieldSchema(type="object", description="Creator details"),
        "column_values": ReturnFieldSchema(
            type="array",
            description="All column values with id, title, type, text, value",
        ),
        "board": ReturnFieldSchema(type="object", description="Parent board details"),
        "group": ReturnFieldSchema(type="object", description="Parent group details"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Item not found",
            recovery_hint="Verify item_id exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.item.list", "monday.item.create"],
        typically_followed_by=["monday.column.change_value", "monday.update.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ ITEM LIST ============

MONDAY_ITEM_LIST = CapabilitySchema(
    capability_key="monday.item.list",
    service="monday",
    category="items",
    description="List items on Monday.com board with pagination",
    description_detailed=(
        "List all items on a board with pagination support. Returns items with "
        "their column values for filtering and display."
    ),
    parameters={
        "board_id": ParameterSchema(
            type="string",
            required=True,
            description="Board ID to list items from",
            example="1234567890",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max items per page (default: 50, max: 100)",
            example=50,
        ),
        "cursor": ParameterSchema(
            type="string",
            required=False,
            description="Pagination cursor for next page",
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of items in this page"),
        "items": ReturnFieldSchema(
            type="array",
            description="Items with id, name, state, url, created_at, column_values",
        ),
        "cursor": ReturnFieldSchema(
            type="string",
            description="Cursor for next page (null if no more pages)",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Board not found",
            recovery_hint="Verify board_id exists and user has access",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.board.list", "monday.board.get"],
        typically_followed_by=["monday.item.get", "monday.column.change_value"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ ITEM UPDATE ============

MONDAY_ITEM_UPDATE = CapabilitySchema(
    capability_key="monday.item.update",
    service="monday",
    category="items",
    description="Update item name on Monday.com",
    description_detailed=(
        "Update an item's name. To update column values, use "
        "monday.column.change_value or monday.column.change_multiple_values."
    ),
    parameters={
        "item_id": ParameterSchema(
            type="string",
            required=True,
            description="Item ID to update",
            example="9876543210",
        ),
        "item_name": ParameterSchema(
            type="string",
            required=True,
            description="New name for the item",
            example="Review Q4 expenses - Updated",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Updated item ID"),
        "name": ReturnFieldSchema(type="string", description="New item name"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Item not found or invalid name",
            recovery_hint="Verify item_id exists and name is valid",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.item.get"],
        related_capabilities=["monday.column.change_value"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ COLUMN CHANGE VALUE ============

MONDAY_COLUMN_CHANGE_VALUE = CapabilitySchema(
    capability_key="monday.column.change_value",
    service="monday",
    category="columns",
    description="Change single column value on Monday.com item (status, date, text)",
    description_detailed=(
        "Update a single column value for an item. Column value format depends "
        'on column type: {"label": "Done"} for status, {"date": "2025-01-15"} for date, '
        '{"text": "value"} for text.'
    ),
    parameters={
        "board_id": ParameterSchema(
            type="string",
            required=True,
            description="Board ID",
            example="1234567890",
        ),
        "item_id": ParameterSchema(
            type="string",
            required=True,
            description="Item ID to update",
            example="9876543210",
        ),
        "column_id": ParameterSchema(
            type="string",
            required=True,
            description="Column ID to update",
            example="status",
        ),
        "value": ParameterSchema(
            type="object",
            required=True,
            description='JSON value for the column (e.g., {"label": "Done"})',
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Updated item ID"),
        "name": ReturnFieldSchema(type="string", description="Item name"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid column value format",
            recovery_hint="Check column type and provide appropriate value structure",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.item.get", "monday.board.get"],
        related_capabilities=["monday.column.change_multiple_values"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ COLUMN CHANGE MULTIPLE VALUES ============

MONDAY_COLUMN_CHANGE_MULTIPLE_VALUES = CapabilitySchema(
    capability_key="monday.column.change_multiple_values",
    service="monday",
    category="columns",
    description="Change multiple column values on Monday.com item at once",
    description_detailed=(
        "Update multiple column values for an item in a single request. "
        "More efficient than multiple single column updates."
    ),
    parameters={
        "board_id": ParameterSchema(
            type="string",
            required=True,
            description="Board ID",
            example="1234567890",
        ),
        "item_id": ParameterSchema(
            type="string",
            required=True,
            description="Item ID to update",
            example="9876543210",
        ),
        "column_values": ParameterSchema(
            type="object",
            required=True,
            description=(
                "Dictionary of column_id -> value "
                '(e.g., {"status": {"label": "Done"}, "date": {"date": "2025-01-15"}})'
            ),
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Updated item ID"),
        "name": ReturnFieldSchema(type="string", description="Item name"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid column values",
            recovery_hint="Check column types and provide appropriate value structures",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.item.get", "monday.board.get"],
        related_capabilities=["monday.column.change_value"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ UPDATE CREATE ============

MONDAY_UPDATE_CREATE = CapabilitySchema(
    capability_key="monday.update.create",
    service="monday",
    category="updates",
    description="Create update (comment) on Monday.com item",
    description_detailed=(
        "Post an update (comment) on a Monday.com item. Updates appear in "
        "the item's activity feed and can trigger notifications."
    ),
    parameters={
        "item_id": ParameterSchema(
            type="string",
            required=True,
            description="Item ID to comment on",
            example="9876543210",
        ),
        "body": ParameterSchema(
            type="string",
            required=True,
            description="Update text/body",
            example="Invoice approved by finance team.",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Update ID"),
        "body": ReturnFieldSchema(type="string", description="Update body"),
        "creator": ReturnFieldSchema(type="object", description="Creator details"),
        "created_at": ReturnFieldSchema(type="string", description="Creation timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Item not found or empty body",
            recovery_hint="Verify item_id exists and body is not empty",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.item.get", "monday.item.create"],
        typically_followed_by=["monday.update.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ UPDATE LIST ============

MONDAY_UPDATE_LIST = CapabilitySchema(
    capability_key="monday.update.list",
    service="monday",
    category="updates",
    description="Get all updates (comments) on Monday.com item",
    description_detailed=(
        "Retrieve all updates (comments) for a specific item. "
        "Useful for viewing approval history and team discussions."
    ),
    parameters={
        "item_id": ParameterSchema(
            type="string",
            required=True,
            description="Item ID to get updates for",
            example="9876543210",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max updates to return (default: 25)",
            example=25,
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of updates"),
        "updates": ReturnFieldSchema(
            type="array",
            description="Updates with id, body, creator, created_at",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Item not found",
            recovery_hint="Verify item_id exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.item.get", "monday.update.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ USER LIST ============

MONDAY_USER_LIST = CapabilitySchema(
    capability_key="monday.user.list",
    service="monday",
    category="users",
    description="Get users in Monday.com account",
    description_detailed=(
        "List all users in the Monday.com account. Can filter by user kind "
        "(guests, non-guests, pending)."
    ),
    parameters={
        "kind": ParameterSchema(
            type="string",
            required=False,
            description="Filter by user kind (default: all)",
            enum=["all", "non_guests", "guests", "non_pending"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max users to return (default: 50)",
            example=50,
        ),
    },
    returns={
        "count": ReturnFieldSchema(type="integer", description="Number of users"),
        "users": ReturnFieldSchema(
            type="array",
            description="Users with id, name, email, enabled, is_guest, title",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["monday.item.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ USER GET CURRENT ============

MONDAY_USER_GET_CURRENT = CapabilitySchema(
    capability_key="monday.user.get_current",
    service="monday",
    category="users",
    description="Get current authenticated Monday.com user",
    description_detailed=(
        "Get details of the currently authenticated user, including account information."
    ),
    parameters={},
    returns={
        "id": ReturnFieldSchema(type="string", description="User ID"),
        "name": ReturnFieldSchema(type="string", description="User name"),
        "email": ReturnFieldSchema(type="string", description="User email"),
        "title": ReturnFieldSchema(type="string", description="User title"),
        "account": ReturnFieldSchema(
            type="object",
            description="Account details with id, name, slug",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ GROUP CREATE ============

MONDAY_GROUP_CREATE = CapabilitySchema(
    capability_key="monday.group.create",
    service="monday",
    category="groups",
    description="Create group on Monday.com board",
    description_detailed=(
        "Create a new group (section) on a board. Groups help organize "
        "items by category, status, or workflow stage."
    ),
    parameters={
        "board_id": ParameterSchema(
            type="string",
            required=True,
            description="Board ID to create group on",
            example="1234567890",
        ),
        "group_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the new group",
            example="January Invoices",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Created group ID"),
        "title": ReturnFieldSchema(type="string", description="Group title"),
        "color": ReturnFieldSchema(type="string", description="Group color"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Monday.com OAuth token not configured",
            recovery_hint="User must connect Monday.com account to Aleq",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Board not found or invalid group name",
            recovery_hint="Verify board_id exists and group_name is valid",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["monday.board.get"],
        typically_followed_by=["monday.item.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# Export all schemas
MONDAY_SCHEMAS: dict[str, CapabilitySchema] = {
    "monday.board.list": MONDAY_BOARD_LIST,
    "monday.board.get": MONDAY_BOARD_GET,
    "monday.item.create": MONDAY_ITEM_CREATE,
    "monday.item.get": MONDAY_ITEM_GET,
    "monday.item.list": MONDAY_ITEM_LIST,
    "monday.item.update": MONDAY_ITEM_UPDATE,
    "monday.column.change_value": MONDAY_COLUMN_CHANGE_VALUE,
    "monday.column.change_multiple_values": MONDAY_COLUMN_CHANGE_MULTIPLE_VALUES,
    "monday.update.create": MONDAY_UPDATE_CREATE,
    "monday.update.list": MONDAY_UPDATE_LIST,
    "monday.user.list": MONDAY_USER_LIST,
    "monday.user.get_current": MONDAY_USER_GET_CURRENT,
    "monday.group.create": MONDAY_GROUP_CREATE,
}

__all__ = ["MONDAY_SCHEMAS"]
