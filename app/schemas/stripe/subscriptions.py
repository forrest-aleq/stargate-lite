"""
Stripe Subscription Capability Schemas.

Rich metadata for subscription operations.
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

SUBSCRIPTION_CREATE = CapabilitySchema(
    capability_key="stripe.subscription.create",
    service="stripe",
    category="subscriptions",
    description="Create a subscription in Stripe",
    description_detailed=(
        "Creates a new subscription for a customer. Subscriptions automatically charge "
        "customers on a recurring basis. Requires a customer with a payment method."
    ),
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
            example="cus_ABC123",
        ),
        "items": ParameterSchema(
            type="array",
            required=True,
            description="List of subscription items with price IDs",
            items_type="object",
            example=[{"price": "price_ABC123"}],
        ),
        "default_payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method to use for this subscription",
        ),
        "trial_period_days": ParameterSchema(
            type="integer",
            required=False,
            description="Number of trial days before charging",
        ),
        "trial_end": ParameterSchema(
            type="integer",
            required=False,
            description="Unix timestamp when trial ends",
        ),
        "cancel_at_period_end": ParameterSchema(
            type="boolean",
            required=False,
            description="Cancel at end of current period",
            default=False,
        ),
        "billing_cycle_anchor": ParameterSchema(
            type="integer",
            required=False,
            description="Unix timestamp for billing cycle start",
        ),
        "proration_behavior": ParameterSchema(
            type="string",
            required=False,
            description="How to handle prorations",
            enum=["create_prorations", "none", "always_invoice"],
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your own use",
        ),
        "collection_method": ParameterSchema(
            type="string",
            required=False,
            description="How to collect payments",
            enum=["charge_automatically", "send_invoice"],
            default="charge_automatically",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Subscription ID",
            example="sub_ABC123",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Subscription status",
            example="active",
        ),
        "current_period_start": ReturnFieldSchema(
            type="integer",
            description="Start of current billing period",
        ),
        "current_period_end": ReturnFieldSchema(
            type="integer",
            description="End of current billing period",
        ),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
        "items": ReturnFieldSchema(type="object", description="Subscription items"),
        "latest_invoice": ReturnFieldSchema(type="string", description="Latest invoice ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Customer has no payment method or invalid price",
            recovery_hint="Attach payment method to customer first",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=[
            "stripe.customer.create",
            "stripe.paymentmethod.attach",
            "stripe.price.create",
        ],
        typically_followed_by=["stripe.subscription.retrieve", "stripe.invoice.retrieve"],
        related_capabilities=["stripe.subscription.update", "stripe.subscription.cancel"],
    ),
    examples=[
        UsageExample(
            description="Create a subscription with trial",
            args={
                "customer": "cus_ABC123",
                "items": [{"price": "price_monthly"}],
                "trial_period_days": 14,
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

SUBSCRIPTION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.subscription.retrieve",
    service="stripe",
    category="subscriptions",
    description="Retrieve a subscription in Stripe",
    parameters={
        "subscription_id": ParameterSchema(
            type="string",
            required=True,
            description="Subscription ID",
            example="sub_ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Subscription ID"),
        "status": ReturnFieldSchema(
            type="string",
            description="Status (active, past_due, canceled, etc.)",
        ),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
        "current_period_start": ReturnFieldSchema(type="integer", description="Period start"),
        "current_period_end": ReturnFieldSchema(type="integer", description="Period end"),
        "cancel_at_period_end": ReturnFieldSchema(type="boolean", description="Will cancel"),
        "canceled_at": ReturnFieldSchema(type="integer", description="When canceled"),
        "items": ReturnFieldSchema(type="object", description="Subscription items"),
        "latest_invoice": ReturnFieldSchema(type="string", description="Latest invoice"),
        "default_payment_method": ReturnFieldSchema(type="string", description="Payment method"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Subscription not found",
            recovery_hint="Verify subscription_id is correct",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

SUBSCRIPTION_UPDATE = CapabilitySchema(
    capability_key="stripe.subscription.update",
    service="stripe",
    category="subscriptions",
    description="Update a subscription in Stripe",
    description_detailed=(
        "Updates an existing subscription. Can change items (upgrade/downgrade), "
        "payment method, billing settings, and more."
    ),
    parameters={
        "subscription_id": ParameterSchema(
            type="string",
            required=True,
            description="Subscription ID to update",
        ),
        "items": ParameterSchema(
            type="array",
            required=False,
            description="Updated subscription items",
        ),
        "default_payment_method": ParameterSchema(
            type="string",
            required=False,
            description="New default payment method",
        ),
        "cancel_at_period_end": ParameterSchema(
            type="boolean",
            required=False,
            description="Set to cancel at period end",
        ),
        "proration_behavior": ParameterSchema(
            type="string",
            required=False,
            description="How to handle prorations",
            enum=["create_prorations", "none", "always_invoice"],
        ),
        "trial_end": ParameterSchema(
            type="string",
            required=False,
            description="Unix timestamp or 'now' to end trial",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Subscription ID"),
        "status": ReturnFieldSchema(type="string", description="Updated status"),
        "items": ReturnFieldSchema(type="object", description="Updated items"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid update (e.g., canceled subscription)",
            recovery_hint="Check subscription status before updating",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.subscription.retrieve"],
    ),
    idempotent=True,
    has_side_effects=True,
)

SUBSCRIPTION_CANCEL = CapabilitySchema(
    capability_key="stripe.subscription.cancel",
    service="stripe",
    category="subscriptions",
    description="Cancel a subscription in Stripe",
    description_detailed=(
        "Cancels a subscription. By default, cancels immediately. Set "
        "cancel_at_period_end to cancel at the end of the current billing period."
    ),
    parameters={
        "subscription_id": ParameterSchema(
            type="string",
            required=True,
            description="Subscription ID to cancel",
        ),
        "cancel_at_period_end": ParameterSchema(
            type="boolean",
            required=False,
            description="Cancel at end of period instead of immediately",
            default=False,
        ),
        "invoice_now": ParameterSchema(
            type="boolean",
            required=False,
            description="Generate final invoice immediately",
            default=False,
        ),
        "prorate": ParameterSchema(
            type="boolean",
            required=False,
            description="Prorate final invoice",
            default=False,
        ),
        "cancellation_details": ParameterSchema(
            type="object",
            required=False,
            description="Cancellation reason details",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Subscription ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'canceled'"),
        "canceled_at": ReturnFieldSchema(type="integer", description="Cancellation timestamp"),
        "cancel_at_period_end": ReturnFieldSchema(
            type="boolean",
            description="Whether canceling at period end",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Subscription already canceled",
            recovery_hint="Check subscription status first",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.subscription.retrieve"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SUBSCRIPTION_LIST = CapabilitySchema(
    capability_key="stripe.subscription.list",
    service="stripe",
    category="subscriptions",
    description="List subscriptions in Stripe",
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer ID",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["active", "past_due", "unpaid", "canceled", "incomplete", "all"],
        ),
        "price": ParameterSchema(
            type="string",
            required=False,
            description="Filter by price ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return (1-100)",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of subscriptions"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results available"),
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

SUBSCRIPTION_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.subscription.create": SUBSCRIPTION_CREATE,
    "stripe.subscription.retrieve": SUBSCRIPTION_RETRIEVE,
    "stripe.subscription.update": SUBSCRIPTION_UPDATE,
    "stripe.subscription.cancel": SUBSCRIPTION_CANCEL,
    "stripe.subscription.list": SUBSCRIPTION_LIST,
}
