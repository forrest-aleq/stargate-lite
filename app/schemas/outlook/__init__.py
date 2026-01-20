"""
Microsoft Outlook Calendar Capability Schemas.

Rich metadata for Outlook calendar operations via Microsoft Graph API.
Finance teams use Outlook for scheduling meetings, coordinating deadlines, and team availability.

Outlook is a Tier 1 system (75K instances in training data).
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    UsageExample,
    WorkflowHints,
)

# ============ EVENT CREATE ============

OUTLOOK_EVENT_CREATE = CapabilitySchema(
    capability_key="outlook.event.create",
    service="microsoft",
    category="calendar",
    description="Create a calendar event in Outlook",
    description_detailed=(
        "Creates a new calendar event in the user's Outlook calendar. "
        "Supports attendees, location, Teams meetings, and rich text body. "
        "Use for scheduling finance reviews, audit meetings, or deadline reminders."
    ),
    parameters={
        "subject": ParameterSchema(
            type="string",
            required=True,
            description="Event subject/title",
            example="Q4 Financial Review",
        ),
        "start_datetime": ParameterSchema(
            type="string",
            required=True,
            description="Start time in ISO 8601 format",
            example="2025-01-20T14:00:00",
        ),
        "end_datetime": ParameterSchema(
            type="string",
            required=True,
            description="End time in ISO 8601 format",
            example="2025-01-20T15:00:00",
        ),
        "body": ParameterSchema(
            type="string",
            required=False,
            description="Event body/description",
        ),
        "is_html": ParameterSchema(
            type="boolean",
            required=False,
            description="Whether body is HTML (default: false)",
        ),
        "timezone": ParameterSchema(
            type="string",
            required=False,
            description="Timezone (default: Eastern Standard Time)",
            example="Pacific Standard Time",
        ),
        "attendees": ParameterSchema(
            type="array",
            required=False,
            description="List of attendee email addresses",
            items_type="string",
            example=["cfo@company.com", "controller@company.com"],
        ),
        "location": ParameterSchema(
            type="string",
            required=False,
            description="Event location",
            example="Conference Room A",
        ),
        "add_teams_meeting": ParameterSchema(
            type="boolean",
            required=False,
            description="Create Teams meeting link (default: false)",
        ),
    },
    returns={
        "event_id": ReturnFieldSchema(type="string", description="Created event ID"),
        "subject": ReturnFieldSchema(type="string", description="Event subject"),
        "start_time": ReturnFieldSchema(type="string", description="Start time"),
        "end_time": ReturnFieldSchema(type="string", description="End time"),
        "web_link": ReturnFieldSchema(type="string", description="URL to view event in Outlook"),
        "teams_link": ReturnFieldSchema(
            type="string",
            description="Teams meeting join URL (if Teams meeting enabled)",
        ),
        "status": ReturnFieldSchema(type="string", description="Should be 'confirmed'"),
        "attendees": ReturnFieldSchema(
            type="array",
            description="Attendees with email and response_status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid datetime format or missing required fields",
            recovery_hint="Use ISO 8601 format for dates and provide subject",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["outlook.availability.check"],
        typically_followed_by=["outlook.event.list"],
        related_capabilities=["outlook.event.update", "outlook.event.cancel"],
    ),
    examples=[
        UsageExample(
            description="Schedule month-end close meeting with Teams",
            args={
                "subject": "Month-End Close Review",
                "start_datetime": "2025-01-31T16:00:00",
                "end_datetime": "2025-01-31T17:00:00",
                "attendees": ["controller@company.com", "ap@company.com"],
                "add_teams_meeting": True,
                "body": "Review month-end close status and outstanding items.",
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

# ============ EVENT LIST ============

OUTLOOK_EVENT_LIST = CapabilitySchema(
    capability_key="outlook.event.list",
    service="microsoft",
    category="calendar",
    description="List calendar events in a date range",
    description_detailed=(
        "Retrieves calendar events within a specified date range. "
        "Returns event details including attendees, location, and Teams links."
    ),
    parameters={
        "start_datetime": ParameterSchema(
            type="string",
            required=False,
            description="Start of date range (ISO 8601)",
            example="2025-01-01T00:00:00",
        ),
        "end_datetime": ParameterSchema(
            type="string",
            required=False,
            description="End of date range (ISO 8601)",
            example="2025-01-31T23:59:59",
        ),
    },
    returns={
        "events": ReturnFieldSchema(
            type="array",
            description=(
                "Events with event_id, subject, body, start_time, end_time, "
                "location, web_link, organizer, is_online_meeting, teams_link, attendees"
            ),
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of events"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["outlook.event.update", "outlook.event.cancel"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ EVENT UPDATE ============

OUTLOOK_EVENT_UPDATE = CapabilitySchema(
    capability_key="outlook.event.update",
    service="microsoft",
    category="calendar",
    description="Update an existing calendar event",
    description_detailed=(
        "Updates an existing calendar event. Only provided fields are updated. "
        "Attendees receive update notifications automatically."
    ),
    parameters={
        "event_id": ParameterSchema(
            type="string",
            required=True,
            description="Event ID to update",
        ),
        "subject": ParameterSchema(
            type="string",
            required=False,
            description="New event subject",
        ),
        "start_datetime": ParameterSchema(
            type="string",
            required=False,
            description="New start time (ISO 8601)",
        ),
        "end_datetime": ParameterSchema(
            type="string",
            required=False,
            description="New end time (ISO 8601)",
        ),
        "body": ParameterSchema(
            type="string",
            required=False,
            description="New event body",
        ),
        "is_html": ParameterSchema(
            type="boolean",
            required=False,
            description="Whether body is HTML",
        ),
        "timezone": ParameterSchema(
            type="string",
            required=False,
            description="Timezone for new times",
        ),
        "location": ParameterSchema(
            type="string",
            required=False,
            description="New location",
        ),
        "attendees": ParameterSchema(
            type="array",
            required=False,
            description="Updated attendee list (replaces existing)",
            items_type="string",
        ),
    },
    returns={
        "event_id": ReturnFieldSchema(type="string", description="Updated event ID"),
        "subject": ReturnFieldSchema(type="string", description="Event subject"),
        "start_time": ReturnFieldSchema(type="string", description="Start time"),
        "end_time": ReturnFieldSchema(type="string", description="End time"),
        "web_link": ReturnFieldSchema(type="string", description="Event URL"),
        "status": ReturnFieldSchema(type="string", description="Should be 'updated'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="Event not found",
            recovery_hint="Verify event_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["outlook.event.list"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ EVENT CANCEL ============

OUTLOOK_EVENT_CANCEL = CapabilitySchema(
    capability_key="outlook.event.cancel",
    service="microsoft",
    category="calendar",
    description="Cancel a calendar event and notify attendees",
    description_detailed=(
        "Cancels an event and sends cancellation notices to all attendees. "
        "Optionally include a comment explaining the cancellation."
    ),
    parameters={
        "event_id": ParameterSchema(
            type="string",
            required=True,
            description="Event ID to cancel",
        ),
        "comment": ParameterSchema(
            type="string",
            required=False,
            description="Cancellation message to attendees",
            example="Meeting rescheduled to next week",
        ),
    },
    returns={
        "event_id": ReturnFieldSchema(type="string", description="Cancelled event ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'cancelled'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="Event not found or already cancelled",
            recovery_hint="Verify event_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["outlook.event.list"],
        typically_followed_by=["outlook.event.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ AVAILABILITY CHECK ============

OUTLOOK_AVAILABILITY_CHECK = CapabilitySchema(
    capability_key="outlook.availability.check",
    service="microsoft",
    category="calendar",
    description="Check free/busy availability for attendees",
    description_detailed=(
        "Checks the availability of one or more people in a time range. "
        "Returns free/busy status for scheduling meetings when everyone is available."
    ),
    parameters={
        "attendees": ParameterSchema(
            type="array",
            required=True,
            description="Email addresses to check availability for",
            items_type="string",
            example=["cfo@company.com", "controller@company.com"],
        ),
        "start_datetime": ParameterSchema(
            type="string",
            required=True,
            description="Start of range to check (ISO 8601)",
            example="2025-01-20T09:00:00",
        ),
        "end_datetime": ParameterSchema(
            type="string",
            required=True,
            description="End of range to check (ISO 8601)",
            example="2025-01-20T17:00:00",
        ),
        "timezone": ParameterSchema(
            type="string",
            required=False,
            description="Timezone (default: Eastern Standard Time)",
        ),
        "interval_minutes": ParameterSchema(
            type="integer",
            required=False,
            description="Availability check interval in minutes (default: 30)",
        ),
    },
    returns={
        "start_time": ReturnFieldSchema(type="string", description="Range start"),
        "end_time": ReturnFieldSchema(type="string", description="Range end"),
        "attendees": ReturnFieldSchema(
            type="array",
            description=(
                "Attendee availability with email, availability_view "
                "(0=free, 2=busy), and busy_times"
            ),
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["outlook.event.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# Export all schemas
OUTLOOK_SCHEMAS: dict[str, CapabilitySchema] = {
    "outlook.event.create": OUTLOOK_EVENT_CREATE,
    "outlook.event.list": OUTLOOK_EVENT_LIST,
    "outlook.event.update": OUTLOOK_EVENT_UPDATE,
    "outlook.event.cancel": OUTLOOK_EVENT_CANCEL,
    "outlook.availability.check": OUTLOOK_AVAILABILITY_CHECK,
}

__all__ = ["OUTLOOK_SCHEMAS"]
