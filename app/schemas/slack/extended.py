"""
Slack Extended Capability Schemas.

Extended operations: reactions, users, search.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ REACTION ADD ============

REACTION_ADD = CapabilitySchema(
    capability_key="reaction.add",
    service="slack",
    category="reactions",
    description="Add a reaction to a message",
    description_detailed=(
        "Adds an emoji reaction to a message. The emoji name should be "
        "specified without colons (e.g., 'thumbsup' not ':thumbsup:')."
    ),
    parameters={
        "channel_id": ParameterSchema(
            type="string",
            required=True,
            description="Channel ID where the message is",
        ),
        "timestamp": ParameterSchema(
            type="string",
            required=True,
            description="Message timestamp (ts)",
            example="1234567890.123456",
        ),
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Emoji name without colons",
            example="thumbsup",
        ),
    },
    returns={
        "channel_id": ReturnFieldSchema(type="string", description="Channel ID"),
        "timestamp": ReturnFieldSchema(type="string", description="Message timestamp"),
        "reaction": ReturnFieldSchema(type="string", description="Emoji name"),
        "status": ReturnFieldSchema(type="string", description="Should be 'added'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Message not found or already has this reaction",
            recovery_hint="Verify message timestamp and channel",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["channel.history", "message.send"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ REACTION REMOVE ============

REACTION_REMOVE = CapabilitySchema(
    capability_key="reaction.remove",
    service="slack",
    category="reactions",
    description="Remove a reaction from a message",
    description_detailed=("Removes an emoji reaction that was previously added to a message."),
    parameters={
        "channel_id": ParameterSchema(
            type="string",
            required=True,
            description="Channel ID where the message is",
        ),
        "timestamp": ParameterSchema(
            type="string",
            required=True,
            description="Message timestamp (ts)",
        ),
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Emoji name without colons",
        ),
    },
    returns={
        "channel_id": ReturnFieldSchema(type="string", description="Channel ID"),
        "timestamp": ReturnFieldSchema(type="string", description="Message timestamp"),
        "reaction": ReturnFieldSchema(type="string", description="Emoji name"),
        "status": ReturnFieldSchema(type="string", description="Should be 'removed'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["reaction.add"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ USER LIST ============

USER_LIST = CapabilitySchema(
    capability_key="user.list",
    service="slack",
    category="users",
    description="List all users in the workspace",
    description_detailed=(
        "Lists all active users in the Slack workspace. " "Excludes deleted/deactivated users."
    ),
    parameters={
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of users to return",
            default=100,
        ),
    },
    returns={
        "users": ReturnFieldSchema(
            type="array",
            description="List of user objects with id, name, email, is_bot, is_admin",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of users"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["user.info", "message.direct"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ USER INFO ============

USER_INFO = CapabilitySchema(
    capability_key="user.info",
    service="slack",
    category="users",
    description="Get detailed information about a user",
    description_detailed=(
        "Retrieves detailed profile information for a specific Slack user "
        "including name, email, title, phone, and timezone."
    ),
    parameters={
        "user_id": ParameterSchema(
            type="string",
            required=True,
            description="Slack user ID",
            example="U1234567890",
        ),
    },
    returns={
        "user_id": ReturnFieldSchema(type="string", description="User ID"),
        "name": ReturnFieldSchema(type="string", description="Username"),
        "real_name": ReturnFieldSchema(type="string", description="Full name"),
        "display_name": ReturnFieldSchema(type="string", description="Display name"),
        "email": ReturnFieldSchema(type="string", description="Email address"),
        "title": ReturnFieldSchema(type="string", description="Job title"),
        "phone": ReturnFieldSchema(type="string", description="Phone number"),
        "is_bot": ReturnFieldSchema(type="boolean", description="Is a bot"),
        "is_admin": ReturnFieldSchema(type="boolean", description="Is workspace admin"),
        "timezone": ReturnFieldSchema(type="string", description="User timezone"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="User not found",
            recovery_hint="Verify user ID with user.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["user.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ SEARCH MESSAGES ============

SEARCH_MESSAGES = CapabilitySchema(
    capability_key="search.messages",
    service="slack",
    category="search",
    description="Search for messages in the workspace",
    description_detailed=(
        "Searches for messages across the workspace using Slack's search syntax. "
        "Supports operators like 'from:', 'in:', 'has:', etc."
    ),
    parameters={
        "query": ParameterSchema(
            type="string",
            required=True,
            description="Search query (supports Slack search operators)",
            example="from:@john project update",
        ),
        "count": ParameterSchema(
            type="integer",
            required=False,
            description="Number of results to return",
            default=20,
        ),
        "sort": ParameterSchema(
            type="string",
            required=False,
            description="Sort field: timestamp or score",
            default="timestamp",
        ),
        "sort_dir": ParameterSchema(
            type="string",
            required=False,
            description="Sort direction: asc or desc",
            default="desc",
        ),
    },
    returns={
        "query": ReturnFieldSchema(type="string", description="Search query used"),
        "messages": ReturnFieldSchema(
            type="array",
            description="List of matching messages with text, user, channel, permalink",
        ),
        "count": ReturnFieldSchema(type="integer", description="Results returned"),
        "total": ReturnFieldSchema(type="integer", description="Total matches found"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Slack OAuth token not configured",
            recovery_hint="User must add Aleq bot to Slack workspace",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

SLACK_EXTENDED_SCHEMAS: dict[str, CapabilitySchema] = {
    "reaction.add": REACTION_ADD,
    "reaction.remove": REACTION_REMOVE,
    "user.list": USER_LIST,
    "user.info": USER_INFO,
    "search.messages": SEARCH_MESSAGES,
}

__all__ = ["SLACK_EXTENDED_SCHEMAS"]
