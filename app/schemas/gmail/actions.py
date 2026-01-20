"""
Gmail Action Capability Schemas.

Action operations: trash, untrash, star, reply, forward.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ EMAIL TRASH ============

EMAIL_TRASH = CapabilitySchema(
    capability_key="email.trash",
    service="google",
    category="email",
    description="Move email message to trash",
    description_detailed=(
        "Moves an email message to the Trash folder. Messages in Trash "
        "are automatically deleted after 30 days."
    ),
    parameters={
        "message_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail message ID to trash",
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
        "status": ReturnFieldSchema(type="string", description="Should be 'trashed'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["email.read", "email.get_message_full"],
        typically_followed_by=["email.untrash"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ EMAIL UNTRASH ============

EMAIL_UNTRASH = CapabilitySchema(
    capability_key="email.untrash",
    service="google",
    category="email",
    description="Restore email message from trash",
    description_detailed=(
        "Restores an email message from the Trash folder back to its original location."
    ),
    parameters={
        "message_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail message ID to restore",
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
        "status": ReturnFieldSchema(type="string", description="Should be 'restored'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["email.trash"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ EMAIL STAR ============

EMAIL_STAR = CapabilitySchema(
    capability_key="email.star",
    service="google",
    category="email",
    description="Star or unstar an email message",
    description_detailed=(
        "Adds or removes the STARRED label from an email message. "
        "Starred messages appear in the Starred view in Gmail."
    ),
    parameters={
        "message_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail message ID",
        ),
        "starred": ParameterSchema(
            type="boolean",
            required=False,
            description="True to star, False to unstar",
            default=True,
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
        "starred": ReturnFieldSchema(type="boolean", description="New starred status"),
        "status": ReturnFieldSchema(type="string", description="'starred' or 'unstarred'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

# ============ EMAIL REPLY ============

EMAIL_REPLY = CapabilitySchema(
    capability_key="email.reply",
    service="google",
    category="email",
    description="Reply to an email in the same thread",
    description_detailed=(
        "Sends a reply to an existing email thread. The reply is added "
        "to the same conversation thread in Gmail."
    ),
    parameters={
        "thread_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail thread ID to reply to",
        ),
        "to": ParameterSchema(
            type="string",
            required=True,
            description="Recipient email address",
        ),
        "body": ParameterSchema(
            type="string",
            required=False,
            description="Reply body content",
            default="",
        ),
        "subject": ParameterSchema(
            type="string",
            required=False,
            description="Subject line (defaults to 'Re: ')",
        ),
        "is_html": ParameterSchema(
            type="boolean",
            required=False,
            description="Whether body is HTML content",
            default=False,
        ),
    },
    returns={
        "message_id": ReturnFieldSchema(type="string", description="New message ID"),
        "thread_id": ReturnFieldSchema(type="string", description="Thread ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'sent'"),
        "to": ReturnFieldSchema(type="string", description="Recipient"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["email.read", "email.thread.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ EMAIL FORWARD ============

EMAIL_FORWARD = CapabilitySchema(
    capability_key="email.forward",
    service="google",
    category="email",
    description="Forward an email to another recipient",
    description_detailed=(
        "Forwards an email message to a new recipient. Includes the original "
        "message content with forward headers."
    ),
    parameters={
        "message_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail message ID to forward",
        ),
        "to": ParameterSchema(
            type="string",
            required=True,
            description="Recipient email address",
        ),
        "message": ParameterSchema(
            type="string",
            required=False,
            description="Additional message to include above forwarded content",
            default="",
        ),
    },
    returns={
        "message_id": ReturnFieldSchema(type="string", description="New message ID"),
        "thread_id": ReturnFieldSchema(type="string", description="Thread ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'forwarded'"),
        "to": ReturnFieldSchema(type="string", description="Recipient"),
        "original_message_id": ReturnFieldSchema(type="string", description="Original ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["email.read", "email.get_message_full"],
    ),
    idempotent=False,
    has_side_effects=True,
)

GMAIL_ACTION_SCHEMAS: dict[str, CapabilitySchema] = {
    "email.trash": EMAIL_TRASH,
    "email.untrash": EMAIL_UNTRASH,
    "email.star": EMAIL_STAR,
    "email.reply": EMAIL_REPLY,
    "email.forward": EMAIL_FORWARD,
}

__all__ = ["GMAIL_ACTION_SCHEMAS"]
