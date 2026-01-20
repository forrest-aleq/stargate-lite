"""
Gmail Core Capability Schemas.

Core email operations: send, read, draft, get_history, get_message_full,
download_attachment, setup_watch, mark_as_read.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ EMAIL SEND ============

EMAIL_SEND = CapabilitySchema(
    capability_key="email.send",
    service="google",
    category="email",
    description="Send an email via Gmail",
    description_detailed=(
        "Sends an email through the Gmail API. Supports HTML content, "
        "CC/BCC recipients, and file attachments. Requires OAuth authentication."
    ),
    parameters={
        "to": ParameterSchema(
            type="string",
            required=True,
            description="Recipient email address",
            example="recipient@example.com",
        ),
        "subject": ParameterSchema(
            type="string",
            required=True,
            description="Email subject line",
            example="Meeting Follow-up",
        ),
        "body": ParameterSchema(
            type="string",
            required=False,
            description="Email body content",
            default="",
        ),
        "cc": ParameterSchema(
            type="string",
            required=False,
            description="CC recipients (comma-separated)",
        ),
        "bcc": ParameterSchema(
            type="string",
            required=False,
            description="BCC recipients (comma-separated)",
        ),
        "is_html": ParameterSchema(
            type="boolean",
            required=False,
            description="Whether body is HTML content",
            default=False,
        ),
        "attachments": ParameterSchema(
            type="array",
            required=False,
            description="File attachments",
            items_type="object",
            example=[{"filename": "report.pdf", "content": "base64-encoded-data"}],
        ),
    },
    returns={
        "message_id": ReturnFieldSchema(
            type="string",
            description="Gmail message ID",
            example="18abc123def",
        ),
        "thread_id": ReturnFieldSchema(type="string", description="Thread ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'sent'"),
        "to": ReturnFieldSchema(type="string", description="Recipient"),
        "subject": ReturnFieldSchema(type="string", description="Subject"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid email address or missing required fields",
            recovery_hint="Verify email addresses are valid",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["email.read"],
        related_capabilities=["email.draft"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ EMAIL READ ============

EMAIL_READ = CapabilitySchema(
    capability_key="email.read",
    service="google",
    category="email",
    description="Read emails from Gmail",
    description_detailed=(
        "Retrieves emails from Gmail inbox using search queries. "
        "Supports Gmail search operators like from:, to:, subject:, etc."
    ),
    parameters={
        "query": ParameterSchema(
            type="string",
            required=False,
            description="Gmail search query",
            example="from:boss@company.com is:unread",
            default="",
        ),
        "max_results": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of emails to return",
            default=10,
        ),
    },
    returns={
        "emails": ReturnFieldSchema(
            type="array",
            description="List of email objects",
            example=[
                {
                    "message_id": "abc123",
                    "subject": "Meeting",
                    "from": "sender@example.com",
                }
            ],
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of emails"),
        "next_page_token": ReturnFieldSchema(type="string", description="Token for pagination"),
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

# ============ EMAIL DRAFT ============

EMAIL_DRAFT = CapabilitySchema(
    capability_key="email.draft",
    service="google",
    category="email",
    description="Create a draft email in Gmail",
    description_detailed=("Creates a draft email that can be edited and sent later from Gmail."),
    parameters={
        "to": ParameterSchema(
            type="string",
            required=True,
            description="Recipient email address",
        ),
        "subject": ParameterSchema(
            type="string",
            required=True,
            description="Email subject line",
        ),
        "body": ParameterSchema(
            type="string",
            required=False,
            description="Email body content",
            default="",
        ),
    },
    returns={
        "draft_id": ReturnFieldSchema(type="string", description="Draft ID"),
        "message_id": ReturnFieldSchema(type="string", description="Message ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'draft'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["email.send"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ EMAIL GET HISTORY ============

EMAIL_GET_HISTORY = CapabilitySchema(
    capability_key="email.get_history",
    service="google",
    category="email",
    description="Fetch Gmail history changes for incremental sync",
    description_detailed=(
        "Retrieves history of changes since a given history ID. "
        "Used for efficient incremental synchronization with push notifications."
    ),
    parameters={
        "start_history_id": ParameterSchema(
            type="string",
            required=True,
            description="History ID to start from",
        ),
        "max_results": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of history records",
            default=100,
        ),
        "email_address": ParameterSchema(
            type="string",
            required=False,
            description="Email address (use 'me' for authenticated user)",
            default="me",
        ),
    },
    returns={
        "history": ReturnFieldSchema(type="array", description="History records"),
        "history_id": ReturnFieldSchema(type="string", description="Current history ID"),
        "next_page_token": ReturnFieldSchema(type="string", description="Pagination"),
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

# ============ EMAIL GET MESSAGE FULL ============

EMAIL_GET_MESSAGE_FULL = CapabilitySchema(
    capability_key="email.get_message_full",
    service="google",
    category="email",
    description="Get full email message with headers, body, and attachments",
    description_detailed=(
        "Retrieves complete email message including headers, body content, "
        "and attachment metadata (attachments are not downloaded)."
    ),
    parameters={
        "message_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail message ID",
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
        "thread_id": ReturnFieldSchema(type="string", description="Thread ID"),
        "label_ids": ReturnFieldSchema(type="array", description="Label IDs"),
        "headers": ReturnFieldSchema(type="object", description="Email headers"),
        "subject": ReturnFieldSchema(type="string", description="Subject"),
        "from": ReturnFieldSchema(type="string", description="Sender"),
        "to": ReturnFieldSchema(type="string", description="Recipient"),
        "date": ReturnFieldSchema(type="string", description="Date"),
        "body": ReturnFieldSchema(type="string", description="Body content"),
        "attachments": ReturnFieldSchema(type="array", description="Attachment metadata"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["email.read", "email.get_history"],
        typically_followed_by=["email.download_attachment"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ EMAIL DOWNLOAD ATTACHMENT ============

EMAIL_DOWNLOAD_ATTACHMENT = CapabilitySchema(
    capability_key="email.download_attachment",
    service="google",
    category="email",
    description="Download email attachment to specified path",
    description_detailed=("Downloads an email attachment and saves it to the specified file path."),
    parameters={
        "message_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail message ID",
        ),
        "attachment_id": ParameterSchema(
            type="string",
            required=True,
            description="Attachment ID from get_message_full",
        ),
        "output_path": ParameterSchema(
            type="string",
            required=True,
            description="File path to save attachment",
            example="~/Downloads/report.pdf",
        ),
        "email_address": ParameterSchema(
            type="string",
            required=False,
            description="Email address (use 'me' for authenticated user)",
            default="me",
        ),
    },
    returns={
        "output_path": ReturnFieldSchema(type="string", description="Saved file path"),
        "size_bytes": ReturnFieldSchema(type="integer", description="File size"),
        "status": ReturnFieldSchema(type="string", description="Should be 'downloaded'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["email.get_message_full"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ EMAIL SETUP WATCH ============

EMAIL_SETUP_WATCH = CapabilitySchema(
    capability_key="email.setup_watch",
    service="google",
    category="email",
    description="Set up Gmail push notifications watch",
    description_detailed=(
        "Configures Gmail to send push notifications to a Cloud Pub/Sub topic "
        "when new emails arrive. Watch expires after 7 days and must be renewed."
    ),
    parameters={
        "topic_name": ParameterSchema(
            type="string",
            required=True,
            description="Cloud Pub/Sub topic name",
            example="projects/my-project/topics/gmail-notifications",
        ),
        "label_ids": ParameterSchema(
            type="array",
            required=False,
            description="Labels to watch",
            items_type="string",
            default=["INBOX"],
        ),
        "email_address": ParameterSchema(
            type="string",
            required=False,
            description="Email address (use 'me' for authenticated user)",
            default="me",
        ),
    },
    returns={
        "history_id": ReturnFieldSchema(type="string", description="Starting history ID"),
        "expiration": ReturnFieldSchema(type="string", description="Watch expiration"),
        "status": ReturnFieldSchema(type="string", description="Should be 'active'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

# ============ EMAIL MARK AS READ ============

EMAIL_MARK_AS_READ = CapabilitySchema(
    capability_key="email.mark_as_read",
    service="google",
    category="email",
    description="Mark email message as read",
    description_detailed=("Marks an email message as read by removing the UNREAD label."),
    parameters={
        "message_id": ParameterSchema(
            type="string",
            required=True,
            description="Gmail message ID",
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
        "status": ReturnFieldSchema(type="string", description="Should be 'read'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Google OAuth credentials not configured",
            recovery_hint="User must complete Google OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["email.get_message_full"],
    ),
    idempotent=True,
    has_side_effects=True,
)

GMAIL_CORE_SCHEMAS = {
    "email.send": EMAIL_SEND,
    "email.read": EMAIL_READ,
    "email.draft": EMAIL_DRAFT,
    "email.get_history": EMAIL_GET_HISTORY,
    "email.get_message_full": EMAIL_GET_MESSAGE_FULL,
    "email.download_attachment": EMAIL_DOWNLOAD_ATTACHMENT,
    "email.setup_watch": EMAIL_SETUP_WATCH,
    "email.mark_as_read": EMAIL_MARK_AS_READ,
}

__all__ = ["GMAIL_CORE_SCHEMAS"]
