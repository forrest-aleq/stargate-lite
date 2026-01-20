"""
Stripe Terminal Locations & Connection Tokens Capability Schemas.

Rich metadata for Terminal reader deployment locations.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ LOCATIONS ============

LOCATION_CREATE = CapabilitySchema(
    capability_key="stripe.terminal.location.create",
    service="stripe",
    category="terminal",
    description="Create a Terminal location",
    description_detailed=(
        "Creates a location representing a physical place where Terminal readers "
        "are deployed. Useful for organizing readers across multiple stores."
    ),
    parameters={
        "display_name": ParameterSchema(
            type="string",
            required=True,
            description="Name displayed in Dashboard",
            example="Main Store",
        ),
        "address": ParameterSchema(
            type="object",
            required=True,
            description="Physical address",
            example={
                "line1": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94102",
                "country": "US",
            },
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Location ID",
            example="tml_ABC123",
        ),
        "display_name": ReturnFieldSchema(type="string", description="Name"),
        "address": ReturnFieldSchema(type="object", description="Address"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

LOCATION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.terminal.location.retrieve",
    service="stripe",
    category="terminal",
    description="Retrieve a Terminal location",
    parameters={
        "location_id": ParameterSchema(
            type="string",
            required=True,
            description="Location ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Location ID"),
        "display_name": ReturnFieldSchema(type="string", description="Name"),
        "address": ReturnFieldSchema(type="object", description="Address"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

LOCATION_UPDATE = CapabilitySchema(
    capability_key="stripe.terminal.location.update",
    service="stripe",
    category="terminal",
    description="Update a Terminal location",
    parameters={
        "location_id": ParameterSchema(
            type="string",
            required=True,
            description="Location ID to update",
        ),
        "display_name": ParameterSchema(
            type="string",
            required=False,
            description="New name",
        ),
        "address": ParameterSchema(
            type="object",
            required=False,
            description="Updated address",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Location ID"),
        "display_name": ReturnFieldSchema(type="string", description="Updated name"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

LOCATION_DELETE = CapabilitySchema(
    capability_key="stripe.terminal.location.delete",
    service="stripe",
    category="terminal",
    description="Delete a Terminal location",
    parameters={
        "location_id": ParameterSchema(
            type="string",
            required=True,
            description="Location ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted location ID"),
        "deleted": ReturnFieldSchema(type="boolean", description="True if deleted"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Location has readers assigned",
            recovery_hint="Reassign or delete readers first",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

LOCATION_LIST = CapabilitySchema(
    capability_key="stripe.terminal.location.list",
    service="stripe",
    category="terminal",
    description="List Terminal locations",
    parameters={
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of locations"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ CONNECTION TOKEN ============

CONNECTION_TOKEN_CREATE = CapabilitySchema(
    capability_key="stripe.terminal.connection_token.create",
    service="stripe",
    category="terminal",
    description="Create a Terminal connection token",
    description_detailed=(
        "Creates a connection token for the Terminal SDK. Tokens are used "
        "to connect your application to Terminal readers."
    ),
    parameters={
        "location": ParameterSchema(
            type="string",
            required=False,
            description="Location to scope the token to",
        ),
    },
    returns={
        "secret": ReturnFieldSchema(type="string", description="Connection token"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

TERMINAL_LOCATION_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.terminal.location.create": LOCATION_CREATE,
    "stripe.terminal.location.retrieve": LOCATION_RETRIEVE,
    "stripe.terminal.location.update": LOCATION_UPDATE,
    "stripe.terminal.location.delete": LOCATION_DELETE,
    "stripe.terminal.location.list": LOCATION_LIST,
    "stripe.terminal.connection_token.create": CONNECTION_TOKEN_CREATE,
}
