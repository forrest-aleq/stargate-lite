"""
Slack Messaging Capability Schemas.

Core messaging operations: send, direct message, file upload.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ MESSAGE SEND ============

MESSAGE_SEND = CapabilitySchema(
    capability_key="message.send",
    service="slack",
    category="messaging",
    description="Send a message to a Slack channel",
    description_detailed=(
        "Posts a message to a Slack channel. Supports rich formatting "
        "with Block Kit and threaded replies."
    ),
    parameters={
        "channel": ParameterSchema(
            type="string",
            required=True,
            description="Channel ID or name (e.g., C1234567890 or #general)",
            example="C1234567890",
        ),
        "text": ParameterSchema(
            type="string",
            required=True,
            description="Message text content",
            example="Hello team!",
        ),
        "blocks": ParameterSchema(
            type="array",
            required=False,
            description="Block Kit blocks for rich formatting",
            items_type="object",
        ),
        "thread_ts": ParameterSchema(
            type="string",
            required=False,
            description="Thread timestamp to reply to",
        ),
    },
    returns={
        "message_id": ReturnFieldSchema(
            type="string",
            description="Message timestamp (ts)",
            example="1234567890.123456",
        ),
        "channel": ReturnFieldSchema(type="string", description="Channel ID"),
        "text": ReturnFieldSchema(type="string", description="Message text"),
        "status": ReturnFieldSchema(type="string", description="Should be 'sent'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Channel not found or bot not in channel",
            recovery_hint="Verify channel exists and bot has access",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["channel.history"],
        related_capabilities=["message.direct"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ MESSAGE DIRECT ============

MESSAGE_DIRECT = CapabilitySchema(
    capability_key="message.direct",
    service="slack",
    category="messaging",
    description="Send a direct message on Slack",
    description_detailed=(
        "Opens a DM conversation with a user and sends a message. "
        "Creates the DM channel if it doesn't exist."
    ),
    parameters={
        "user_id": ParameterSchema(
            type="string",
            required=True,
            description="Slack user ID to message",
            example="U1234567890",
        ),
        "text": ParameterSchema(
            type="string",
            required=True,
            description="Message text content",
        ),
    },
    returns={
        "message_id": ReturnFieldSchema(type="string", description="Message timestamp"),
        "channel": ReturnFieldSchema(type="string", description="DM channel ID"),
        "text": ReturnFieldSchema(type="string", description="Message text"),
        "status": ReturnFieldSchema(type="string", description="Should be 'sent'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="User not found",
            recovery_hint="Verify user ID is correct",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

# ============ FILE UPLOAD ============

FILE_UPLOAD = CapabilitySchema(
    capability_key="file.upload",
    service="slack",
    category="files",
    description="Upload a file to Slack",
    description_detailed=(
        "Uploads a file to one or more Slack channels. "
        "Can include an initial comment with the file."
    ),
    parameters={
        "channels": ParameterSchema(
            type="string",
            required=True,
            description="Comma-separated channel IDs to share to",
            example="C1234567890,C0987654321",
        ),
        "content": ParameterSchema(
            type="string",
            required=True,
            description="File content (base64 encoded or raw text)",
        ),
        "filename": ParameterSchema(
            type="string",
            required=True,
            description="Name for the file",
            example="report.csv",
        ),
        "title": ParameterSchema(
            type="string",
            required=False,
            description="Title for the file (defaults to filename)",
        ),
        "initial_comment": ParameterSchema(
            type="string",
            required=False,
            description="Message to post with the file",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(type="string", description="File ID"),
        "filename": ReturnFieldSchema(type="string", description="File name"),
        "url": ReturnFieldSchema(type="string", description="Private file URL"),
        "status": ReturnFieldSchema(type="string", description="Should be 'uploaded'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

SLACK_MESSAGING_SCHEMAS: dict[str, CapabilitySchema] = {
    "message.send": MESSAGE_SEND,
    "message.direct": MESSAGE_DIRECT,
    "file.upload": FILE_UPLOAD,
}

__all__ = ["SLACK_MESSAGING_SCHEMAS"]
