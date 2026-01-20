"""
Stripe Radar Value Lists Capability Schemas.

Rich metadata for fraud prevention rule lists.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ VALUE LISTS ============

VALUE_LIST_CREATE = CapabilitySchema(
    capability_key="stripe.radar.value_list.create",
    service="stripe",
    category="radar",
    description="Create a Radar value list",
    description_detailed=(
        "Creates a value list for use in Radar rules. Value lists can contain "
        "email addresses, IP addresses, card fingerprints, or strings."
    ),
    parameters={
        "alias": ParameterSchema(
            type="string",
            required=True,
            description="Unique identifier for the list",
            example="blocked_emails",
        ),
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Display name for the list",
            example="Blocked Email Addresses",
        ),
        "item_type": ParameterSchema(
            type="string",
            required=True,
            description="Type of items in the list",
            enum=[
                "card_fingerprint",
                "card_bin",
                "email",
                "ip_address",
                "country",
                "string",
                "case_sensitive_string",
                "customer_id",
                "sepa_debit_fingerprint",
            ],
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
            description="Value list ID",
            example="rsl_ABC123",
        ),
        "alias": ReturnFieldSchema(type="string", description="Alias"),
        "name": ReturnFieldSchema(type="string", description="Name"),
        "item_type": ReturnFieldSchema(type="string", description="Item type"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Alias already exists",
            recovery_hint="Use a unique alias",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

VALUE_LIST_RETRIEVE = CapabilitySchema(
    capability_key="stripe.radar.value_list.retrieve",
    service="stripe",
    category="radar",
    description="Retrieve a Radar value list",
    parameters={
        "value_list_id": ParameterSchema(
            type="string",
            required=True,
            description="Value list ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="List ID"),
        "alias": ReturnFieldSchema(type="string", description="Alias"),
        "name": ReturnFieldSchema(type="string", description="Name"),
        "item_type": ReturnFieldSchema(type="string", description="Item type"),
        "list_items": ReturnFieldSchema(type="object", description="Items in list"),
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

VALUE_LIST_UPDATE = CapabilitySchema(
    capability_key="stripe.radar.value_list.update",
    service="stripe",
    category="radar",
    description="Update a Radar value list",
    parameters={
        "value_list_id": ParameterSchema(
            type="string",
            required=True,
            description="Value list ID to update",
        ),
        "name": ParameterSchema(
            type="string",
            required=False,
            description="New name",
        ),
        "alias": ParameterSchema(
            type="string",
            required=False,
            description="New alias",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="List ID"),
        "name": ReturnFieldSchema(type="string", description="Updated name"),
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

VALUE_LIST_DELETE = CapabilitySchema(
    capability_key="stripe.radar.value_list.delete",
    service="stripe",
    category="radar",
    description="Delete a Radar value list",
    parameters={
        "value_list_id": ParameterSchema(
            type="string",
            required=True,
            description="Value list ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted list ID"),
        "deleted": ReturnFieldSchema(type="boolean", description="True if deleted"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="List is used in rules",
            recovery_hint="Remove from rules first",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

VALUE_LIST_LIST = CapabilitySchema(
    capability_key="stripe.radar.value_list.list",
    service="stripe",
    category="radar",
    description="List Radar value lists",
    parameters={
        "alias": ParameterSchema(
            type="string",
            required=False,
            description="Filter by alias",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of value lists"),
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

# ============ VALUE LIST ITEMS ============

VALUE_LIST_ITEM_CREATE = CapabilitySchema(
    capability_key="stripe.radar.value_list_item.create",
    service="stripe",
    category="radar",
    description="Add an item to a Radar value list",
    parameters={
        "value_list": ParameterSchema(
            type="string",
            required=True,
            description="Value list ID",
        ),
        "value": ParameterSchema(
            type="string",
            required=True,
            description="Value to add",
            example="blocked@example.com",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Item ID"),
        "value": ReturnFieldSchema(type="string", description="Value"),
        "value_list": ReturnFieldSchema(type="string", description="List ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Value already exists or invalid format",
            recovery_hint="Check value format matches list item_type",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

VALUE_LIST_ITEM_RETRIEVE = CapabilitySchema(
    capability_key="stripe.radar.value_list_item.retrieve",
    service="stripe",
    category="radar",
    description="Retrieve a value list item",
    parameters={
        "item_id": ParameterSchema(
            type="string",
            required=True,
            description="Item ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Item ID"),
        "value": ReturnFieldSchema(type="string", description="Value"),
        "value_list": ReturnFieldSchema(type="string", description="List ID"),
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

VALUE_LIST_ITEM_DELETE = CapabilitySchema(
    capability_key="stripe.radar.value_list_item.delete",
    service="stripe",
    category="radar",
    description="Delete a value list item",
    parameters={
        "item_id": ParameterSchema(
            type="string",
            required=True,
            description="Item ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted item ID"),
        "deleted": ReturnFieldSchema(type="boolean", description="True if deleted"),
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

VALUE_LIST_ITEM_LIST = CapabilitySchema(
    capability_key="stripe.radar.value_list_item.list",
    service="stripe",
    category="radar",
    description="List items in a value list",
    parameters={
        "value_list": ParameterSchema(
            type="string",
            required=True,
            description="Value list ID",
        ),
        "value": ParameterSchema(
            type="string",
            required=False,
            description="Filter by value",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of items"),
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

VALUE_LIST_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.radar.value_list.create": VALUE_LIST_CREATE,
    "stripe.radar.value_list.retrieve": VALUE_LIST_RETRIEVE,
    "stripe.radar.value_list.update": VALUE_LIST_UPDATE,
    "stripe.radar.value_list.delete": VALUE_LIST_DELETE,
    "stripe.radar.value_list.list": VALUE_LIST_LIST,
    "stripe.radar.value_list_item.create": VALUE_LIST_ITEM_CREATE,
    "stripe.radar.value_list_item.retrieve": VALUE_LIST_ITEM_RETRIEVE,
    "stripe.radar.value_list_item.delete": VALUE_LIST_ITEM_DELETE,
    "stripe.radar.value_list_item.list": VALUE_LIST_ITEM_LIST,
}
