"""
Slack Channel Capability Schemas.

Channel operations: create, invite, history, list, archive, topic.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ CHANNEL CREATE ============

CHANNEL_CREATE = CapabilitySchema(
    capability_key="channel.create",
    service="slack",
    category="channels",
    description="Create a Slack channel",
    description_detailed=(
        "Creates a new public or private Slack channel. "
        "Channel names must be lowercase, without spaces."
    ),
    parameters={
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Channel name (lowercase, no spaces)",
            example="project-alpha",
        ),
        "is_private": ParameterSchema(
            type="boolean",
            required=False,
            description="Create as private channel",
            default=False,
        ),
    },
    returns={
        "channel_id": ReturnFieldSchema(type="string", description="Channel ID"),
        "channel_name": ReturnFieldSchema(type="string", description="Channel name"),
        "is_private": ReturnFieldSchema(type="boolean", description="Private status"),
        "status": ReturnFieldSchema(type="string", description="Should be 'created'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Channel name already exists or invalid",
            recovery_hint="Use unique name with lowercase letters and hyphens",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["channel.invite", "message.send"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ CHANNEL INVITE ============

CHANNEL_INVITE = CapabilitySchema(
    capability_key="channel.invite",
    service="slack",
    category="channels",
    description="Invite users to a Slack channel",
    description_detailed=(
        "Invites one or more users to a Slack channel. Users must be part of the workspace."
    ),
    parameters={
        "channel_id": ParameterSchema(
            type="string",
            required=True,
            description="Channel ID to invite to",
        ),
        "user_ids": ParameterSchema(
            type="string",
            required=True,
            description="Comma-separated user IDs to invite",
            example="U1234567890,U0987654321",
        ),
    },
    returns={
        "channel_id": ReturnFieldSchema(type="string", description="Channel ID"),
        "invited_users": ReturnFieldSchema(type="string", description="Invited users"),
        "status": ReturnFieldSchema(type="string", description="Should be 'invited'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="User already in channel or user not found",
            recovery_hint="Verify user IDs and channel membership",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["channel.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ CHANNEL HISTORY ============

CHANNEL_HISTORY = CapabilitySchema(
    capability_key="channel.history",
    service="slack",
    category="channels",
    description="Get message history from a Slack channel",
    description_detailed=(
        "Retrieves recent messages from a Slack channel. "
        "Returns messages in reverse chronological order."
    ),
    parameters={
        "channel_id": ParameterSchema(
            type="string",
            required=True,
            description="Channel ID to get history from",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of messages to return",
            default=100,
        ),
    },
    returns={
        "channel_id": ReturnFieldSchema(type="string", description="Channel ID"),
        "messages": ReturnFieldSchema(
            type="array",
            description="List of messages",
            example=[{"text": "Hello", "user": "U123", "timestamp": "1234567890.123"}],
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of messages"),
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
    idempotent=True,
    has_side_effects=False,
)

# ============ CHANNEL LIST ============

CHANNEL_LIST = CapabilitySchema(
    capability_key="channel.list",
    service="slack",
    category="channels",
    description="List all channels in the workspace",
    description_detailed=(
        "Lists all channels in the Slack workspace that the bot has access to. "
        "Can filter by public/private channels."
    ),
    parameters={
        "types": ParameterSchema(
            type="string",
            required=False,
            description="Comma-separated channel types: public_channel, private_channel",
            default="public_channel,private_channel",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of channels to return",
            default=100,
        ),
    },
    returns={
        "channels": ReturnFieldSchema(
            type="array",
            description="List of channel objects with id, name, is_private, is_archived",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of channels"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["channel.history", "message.send"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ CHANNEL ARCHIVE ============

CHANNEL_ARCHIVE = CapabilitySchema(
    capability_key="channel.archive",
    service="slack",
    category="channels",
    description="Archive a Slack channel",
    description_detailed=(
        "Archives a Slack channel. Archived channels are hidden from the channel list "
        "but can be unarchived later. Requires appropriate permissions."
    ),
    parameters={
        "channel_id": ParameterSchema(
            type="string",
            required=True,
            description="Channel ID to archive",
        ),
    },
    returns={
        "channel_id": ReturnFieldSchema(type="string", description="Channel ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'archived'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Channel not found or insufficient permissions",
            recovery_hint="Verify channel exists and bot has admin access",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

# ============ CHANNEL TOPIC ============

CHANNEL_TOPIC = CapabilitySchema(
    capability_key="channel.topic",
    service="slack",
    category="channels",
    description="Set the topic for a Slack channel",
    description_detailed=(
        "Sets or updates the topic for a Slack channel. "
        "The topic is displayed at the top of the channel."
    ),
    parameters={
        "channel_id": ParameterSchema(
            type="string",
            required=True,
            description="Channel ID to update",
        ),
        "topic": ParameterSchema(
            type="string",
            required=True,
            description="New topic text",
            example="Weekly team sync discussions",
        ),
    },
    returns={
        "channel_id": ReturnFieldSchema(type="string", description="Channel ID"),
        "topic": ReturnFieldSchema(type="string", description="New topic"),
        "status": ReturnFieldSchema(type="string", description="Should be 'updated'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["channel.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

SLACK_CHANNEL_SCHEMAS: dict[str, CapabilitySchema] = {
    "channel.create": CHANNEL_CREATE,
    "channel.invite": CHANNEL_INVITE,
    "channel.history": CHANNEL_HISTORY,
    "channel.list": CHANNEL_LIST,
    "channel.archive": CHANNEL_ARCHIVE,
    "channel.topic": CHANNEL_TOPIC,
}

__all__ = ["SLACK_CHANNEL_SCHEMAS"]
