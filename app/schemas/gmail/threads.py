"""
Gmail Label and Thread Capability Schemas.

Label operations: list, create, apply.
Thread operations: get, list.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ EMAIL LABEL LIST ============

EMAIL_LABEL_LIST = CapabilitySchema(
    capability_key="email.label.list",
    service="google",
    category="email",
    description="List all labels in the mailbox",
    description_detailed=(
        "Retrieves all labels in the Gmail mailbox, including system labels "
        "(INBOX, SENT, TRASH, etc.) and user-created labels."
    ),
    parameters={
        "email_address": ParameterSchema(
            type="string",
            required=False,
            description="Email address (use 'me' for authenticated user)",
            default="me",
        ),
    },
    returns={
        "labels": ReturnFieldSchema(
            type="array",
            description="List of label objects with id, name, and type",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of labels"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ EMAIL LABEL CREATE ============

EMAIL_LABEL_CREATE = CapabilitySchema(
    capability_key="email.label.create",
    service="google",
    category="email",
    description="Create a new label",
    description_detailed=("Creates a new user label in Gmail for organizing messages."),
    parameters={
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Label name",
            example="Projects/Important",
        ),
        "visibility": ParameterSchema(
            type="string",
            required=False,
            description="Label visibility: labelShow, labelShowIfUnread, or labelHide",
            default="labelShow",
        ),
        "message_visibility": ParameterSchema(
            type="string",
            required=False,
            description="Message list visibility: show or hide",
            default="show",
        ),
        "email_address": ParameterSchema(
            type="string",
            required=False,
            description="Email address (use 'me' for authenticated user)",
            default="me",
        ),
    },
    returns={
        "label_id": ReturnFieldSchema(type="string", description="New label ID"),
        "name": ReturnFieldSchema(type="string", description="Label name"),
        "type": ReturnFieldSchema(type="string", description="Label type (user)"),
        "status": ReturnFieldSchema(type="string", description="Should be 'created'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Label name already exists",
            recovery_hint="Use email.label.list to check existing labels",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["email.label.apply"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ EMAIL LABEL APPLY ============

EMAIL_LABEL_APPLY = CapabilitySchema(
    capability_key="email.label.apply",
    service="google",
    category="email",
    description="Apply or remove labels from a message",
    description_detailed=(
        "Modifies the labels on an email message. Can add and remove "
        "multiple labels in a single operation."
    ),
    parameters={
        "message_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail message ID",
        ),
        "add_label_ids": ParameterSchema(
            type="array",
            required=False,
            description="Label IDs to add",
            items_type="string",
        ),
        "remove_label_ids": ParameterSchema(
            type="array",
            required=False,
            description="Label IDs to remove",
            items_type="string",
        ),
        "email_address": ParameterSchema(
            type="string",
            required=False,
            description="Email address (use 'me' for authenticated user)",
            default="me",
        ),
    },
    returns={
        "message_id": ReturnFieldSchema(type="string", description="Message ID"),
        "added_labels": ReturnFieldSchema(type="array", description="Labels added"),
        "removed_labels": ReturnFieldSchema(type="array", description="Labels removed"),
        "status": ReturnFieldSchema(type="string", description="Should be 'modified'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["email.label.list", "email.read"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ EMAIL THREAD GET ============

EMAIL_THREAD_GET = CapabilitySchema(
    capability_key="email.thread.get",
    service="google",
    category="email",
    description="Get a full email thread with all messages",
    description_detailed=(
        "Retrieves a complete email thread including all messages in the conversation. "
        "Useful for understanding the full context of an email exchange."
    ),
    parameters={
        "thread_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail thread ID",
        ),
        "email_address": ParameterSchema(
            type="string",
            required=False,
            description="Email address (use 'me' for authenticated user)",
            default="me",
        ),
    },
    returns={
        "thread_id": ReturnFieldSchema(type="string", description="Thread ID"),
        "messages": ReturnFieldSchema(
            type="array",
            description="List of messages in the thread with full content",
        ),
        "message_count": ReturnFieldSchema(type="integer", description="Number of messages"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["email.read", "email.thread.list"],
        typically_followed_by=["email.reply"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ EMAIL THREAD LIST ============

EMAIL_THREAD_LIST = CapabilitySchema(
    capability_key="email.thread.list",
    service="google",
    category="email",
    description="List email threads",
    description_detailed=(
        "Lists email threads matching a search query. Threads group related "
        "messages together (like email conversations in Gmail)."
    ),
    parameters={
        "query": ParameterSchema(
            type="string",
            required=False,
            description="Gmail search query",
            example="from:boss@company.com",
            default="",
        ),
        "max_results": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of threads to return",
            default=20,
        ),
        "email_address": ParameterSchema(
            type="string",
            required=False,
            description="Email address (use 'me' for authenticated user)",
            default="me",
        ),
    },
    returns={
        "threads": ReturnFieldSchema(
            type="array",
            description="List of thread objects with id and snippet",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of threads"),
        "next_page_token": ReturnFieldSchema(type="string", description="Pagination token"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["email.thread.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

GMAIL_THREAD_SCHEMAS: dict[str, CapabilitySchema] = {
    "email.label.list": EMAIL_LABEL_LIST,
    "email.label.create": EMAIL_LABEL_CREATE,
    "email.label.apply": EMAIL_LABEL_APPLY,
    "email.thread.get": EMAIL_THREAD_GET,
    "email.thread.list": EMAIL_THREAD_LIST,
}

__all__ = ["GMAIL_THREAD_SCHEMAS"]
