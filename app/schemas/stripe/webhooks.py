"""
Stripe Webhook Capability Schemas.

Rich metadata for webhook endpoints and event handling.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

WEBHOOK_ENDPOINT_CREATE = CapabilitySchema(
    capability_key="stripe.webhook.create",
    service="stripe",
    category="webhooks",
    description="Create a webhook endpoint in Stripe",
    description_detailed=(
        "Creates a webhook endpoint that Stripe will send events to. "
        "Webhooks notify your application of events like successful payments, "
        "subscription changes, and dispute updates."
    ),
    parameters={
        "url": ParameterSchema(
            type="string",
            required=True,
            description="URL that receives webhook events",
            example="https://example.com/webhooks/stripe",
        ),
        "enabled_events": ParameterSchema(
            type="array",
            required=True,
            description="Events to send to this endpoint",
            items_type="string",
            example=["payment_intent.succeeded", "customer.subscription.updated"],
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Description of the webhook endpoint",
        ),
        "api_version": ParameterSchema(
            type="string",
            required=False,
            description="Stripe API version for events",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your use",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Webhook endpoint ID",
            example="we_ABC123",
        ),
        "url": ReturnFieldSchema(type="string", description="Endpoint URL"),
        "status": ReturnFieldSchema(type="string", description="Endpoint status"),
        "secret": ReturnFieldSchema(type="string", description="Signing secret"),
        "enabled_events": ReturnFieldSchema(type="array", description="Enabled events"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid URL or event names",
            recovery_hint="Verify URL is HTTPS and event names are valid",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

WEBHOOK_ENDPOINT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.webhook.retrieve",
    service="stripe",
    category="webhooks",
    description="Retrieve a webhook endpoint",
    parameters={
        "webhook_endpoint_id": ParameterSchema(
            type="string",
            required=True,
            description="Webhook endpoint ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Endpoint ID"),
        "url": ReturnFieldSchema(type="string", description="Endpoint URL"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "enabled_events": ReturnFieldSchema(type="array", description="Events"),
        "api_version": ReturnFieldSchema(type="string", description="API version"),
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

WEBHOOK_ENDPOINT_UPDATE = CapabilitySchema(
    capability_key="stripe.webhook.update",
    service="stripe",
    category="webhooks",
    description="Update a webhook endpoint",
    parameters={
        "webhook_endpoint_id": ParameterSchema(
            type="string",
            required=True,
            description="Webhook endpoint ID to update",
        ),
        "url": ParameterSchema(
            type="string",
            required=False,
            description="New URL",
        ),
        "enabled_events": ParameterSchema(
            type="array",
            required=False,
            description="Updated event list",
        ),
        "disabled": ParameterSchema(
            type="boolean",
            required=False,
            description="Disable the endpoint",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Update description",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Endpoint ID"),
        "url": ReturnFieldSchema(type="string", description="Updated URL"),
        "status": ReturnFieldSchema(type="string", description="Status"),
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

WEBHOOK_ENDPOINT_DELETE = CapabilitySchema(
    capability_key="stripe.webhook.delete",
    service="stripe",
    category="webhooks",
    description="Delete a webhook endpoint",
    parameters={
        "webhook_endpoint_id": ParameterSchema(
            type="string",
            required=True,
            description="Webhook endpoint ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted endpoint ID"),
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

WEBHOOK_ENDPOINT_LIST = CapabilitySchema(
    capability_key="stripe.webhook.list",
    service="stripe",
    category="webhooks",
    description="List webhook endpoints",
    parameters={
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of endpoints"),
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

EVENT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.event.retrieve",
    service="stripe",
    category="webhooks",
    description="Retrieve a Stripe event",
    description_detailed=(
        "Retrieves the details of an event. Events are created when something "
        "interesting happens in your account (payment succeeds, subscription renews, etc)."
    ),
    parameters={
        "event_id": ParameterSchema(
            type="string",
            required=True,
            description="Event ID",
            example="evt_ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Event ID"),
        "type": ReturnFieldSchema(type="string", description="Event type"),
        "data": ReturnFieldSchema(type="object", description="Event data object"),
        "created": ReturnFieldSchema(type="integer", description="Unix timestamp"),
        "livemode": ReturnFieldSchema(type="boolean", description="Live or test"),
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

EVENT_LIST = CapabilitySchema(
    capability_key="stripe.event.list",
    service="stripe",
    category="webhooks",
    description="List Stripe events",
    parameters={
        "type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by event type",
        ),
        "created": ParameterSchema(
            type="object",
            required=False,
            description="Filter by created date (gte, lte)",
        ),
        "delivery_success": ParameterSchema(
            type="boolean",
            required=False,
            description="Filter by delivery status",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of events"),
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

WEBHOOK_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.webhook.create": WEBHOOK_ENDPOINT_CREATE,
    "stripe.webhook.retrieve": WEBHOOK_ENDPOINT_RETRIEVE,
    "stripe.webhook.update": WEBHOOK_ENDPOINT_UPDATE,
    "stripe.webhook.delete": WEBHOOK_ENDPOINT_DELETE,
    "stripe.webhook.list": WEBHOOK_ENDPOINT_LIST,
    "stripe.event.retrieve": EVENT_RETRIEVE,
    "stripe.event.list": EVENT_LIST,
}
