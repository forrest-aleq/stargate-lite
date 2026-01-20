"""
Stripe Billing Portal Capability Schemas.

Rich metadata for customer self-service portal management.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ PORTAL SESSIONS ============

PORTAL_SESSION_CREATE = CapabilitySchema(
    capability_key="stripe.billing_portal.session.create",
    service="stripe",
    category="billing_portal",
    description="Create a billing portal session",
    description_detailed=(
        "Creates a portal session for a customer to manage their subscription, "
        "update payment methods, and view invoices in a self-service interface."
    ),
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
            example="cus_ABC123",
        ),
        "return_url": ParameterSchema(
            type="string",
            required=False,
            description="URL to return to after portal",
            example="https://example.com/account",
        ),
        "configuration": ParameterSchema(
            type="string",
            required=False,
            description="Portal configuration ID",
        ),
        "flow_data": ParameterSchema(
            type="object",
            required=False,
            description="Start portal in specific flow",
            example={
                "type": "subscription_cancel",
                "subscription_cancel": {"subscription": "sub_123"},
            },
        ),
        "locale": ParameterSchema(
            type="string",
            required=False,
            description="Portal language",
        ),
        "on_behalf_of": ParameterSchema(
            type="string",
            required=False,
            description="Connected account (for Connect)",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Portal session ID",
            example="bps_ABC123",
        ),
        "url": ReturnFieldSchema(type="string", description="Portal URL"),
        "return_url": ReturnFieldSchema(type="string", description="Return URL"),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
        "configuration": ReturnFieldSchema(type="string", description="Config ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Customer not found or no configuration",
            recovery_hint="Verify customer exists and portal is configured",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

# ============ PORTAL CONFIGURATIONS ============

PORTAL_CONFIGURATION_CREATE = CapabilitySchema(
    capability_key="stripe.billing_portal.configuration.create",
    service="stripe",
    category="billing_portal",
    description="Create a billing portal configuration",
    description_detailed=(
        "Creates a configuration defining what customers can do in the portal, "
        "such as updating subscriptions, payment methods, or viewing invoices."
    ),
    parameters={
        "business_profile": ParameterSchema(
            type="object",
            required=True,
            description="Business info shown in portal",
            example={
                "headline": "Manage your subscription",
                "privacy_policy_url": "https://example.com/privacy",
                "terms_of_service_url": "https://example.com/terms",
            },
        ),
        "features": ParameterSchema(
            type="object",
            required=True,
            description="Portal features configuration",
            example={
                "customer_update": {"enabled": True, "allowed_updates": ["email", "tax_id"]},
                "invoice_history": {"enabled": True},
                "payment_method_update": {"enabled": True},
                "subscription_cancel": {"enabled": True, "mode": "at_period_end"},
            },
        ),
        "default_return_url": ParameterSchema(
            type="string",
            required=False,
            description="Default return URL",
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
            description="Configuration ID",
            example="bpc_ABC123",
        ),
        "is_default": ReturnFieldSchema(type="boolean", description="Is default config"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "features": ReturnFieldSchema(type="object", description="Features config"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid features configuration",
            recovery_hint="Check features object structure",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

PORTAL_CONFIGURATION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.billing_portal.configuration.retrieve",
    service="stripe",
    category="billing_portal",
    description="Retrieve a billing portal configuration",
    parameters={
        "configuration_id": ParameterSchema(
            type="string",
            required=True,
            description="Configuration ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Configuration ID"),
        "is_default": ReturnFieldSchema(type="boolean", description="Is default"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "business_profile": ReturnFieldSchema(type="object", description="Business info"),
        "features": ReturnFieldSchema(type="object", description="Features"),
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

PORTAL_CONFIGURATION_UPDATE = CapabilitySchema(
    capability_key="stripe.billing_portal.configuration.update",
    service="stripe",
    category="billing_portal",
    description="Update a billing portal configuration",
    parameters={
        "configuration_id": ParameterSchema(
            type="string",
            required=True,
            description="Configuration ID to update",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Activate or deactivate",
        ),
        "business_profile": ParameterSchema(
            type="object",
            required=False,
            description="Update business info",
        ),
        "features": ParameterSchema(
            type="object",
            required=False,
            description="Update features",
        ),
        "default_return_url": ParameterSchema(
            type="string",
            required=False,
            description="Update return URL",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Configuration ID"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
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

PORTAL_CONFIGURATION_LIST = CapabilitySchema(
    capability_key="stripe.billing_portal.configuration.list",
    service="stripe",
    category="billing_portal",
    description="List billing portal configurations",
    parameters={
        "is_default": ParameterSchema(
            type="boolean",
            required=False,
            description="Filter by default status",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Filter by active status",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of configurations"),
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

# ============ CUSTOMER TAX IDS ============

CUSTOMER_TAX_ID_CREATE = CapabilitySchema(
    capability_key="stripe.customer.tax_id.create",
    service="stripe",
    category="billing_portal",
    description="Add a tax ID to a customer",
    description_detailed=(
        "Creates a tax ID for a customer. Tax IDs are used for tax compliance "
        "and appear on invoices."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "type": ParameterSchema(
            type="string",
            required=True,
            description="Type of tax ID",
            example="us_ein",
        ),
        "value": ParameterSchema(
            type="string",
            required=True,
            description="Tax ID value",
            example="12-3456789",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Tax ID object ID"),
        "type": ReturnFieldSchema(type="string", description="Tax ID type"),
        "value": ReturnFieldSchema(type="string", description="Tax ID value"),
        "verification": ReturnFieldSchema(type="object", description="Verification status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid tax ID format",
            recovery_hint="Check tax ID format for the specified type",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

CUSTOMER_TAX_ID_RETRIEVE = CapabilitySchema(
    capability_key="stripe.customer.tax_id.retrieve",
    service="stripe",
    category="billing_portal",
    description="Retrieve a customer tax ID",
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "tax_id": ParameterSchema(
            type="string",
            required=True,
            description="Tax ID object ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Tax ID object ID"),
        "type": ReturnFieldSchema(type="string", description="Type"),
        "value": ReturnFieldSchema(type="string", description="Value"),
        "verification": ReturnFieldSchema(type="object", description="Verification"),
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

CUSTOMER_TAX_ID_DELETE = CapabilitySchema(
    capability_key="stripe.customer.tax_id.delete",
    service="stripe",
    category="billing_portal",
    description="Delete a customer tax ID",
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "tax_id": ParameterSchema(
            type="string",
            required=True,
            description="Tax ID object ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted tax ID"),
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

CUSTOMER_TAX_ID_LIST = CapabilitySchema(
    capability_key="stripe.customer.tax_id.list",
    service="stripe",
    category="billing_portal",
    description="List customer tax IDs",
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of tax IDs"),
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

BILLING_PORTAL_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.billing_portal.session.create": PORTAL_SESSION_CREATE,
    "stripe.billing_portal.configuration.create": PORTAL_CONFIGURATION_CREATE,
    "stripe.billing_portal.configuration.retrieve": PORTAL_CONFIGURATION_RETRIEVE,
    "stripe.billing_portal.configuration.update": PORTAL_CONFIGURATION_UPDATE,
    "stripe.billing_portal.configuration.list": PORTAL_CONFIGURATION_LIST,
    "stripe.customer.tax_id.create": CUSTOMER_TAX_ID_CREATE,
    "stripe.customer.tax_id.retrieve": CUSTOMER_TAX_ID_RETRIEVE,
    "stripe.customer.tax_id.delete": CUSTOMER_TAX_ID_DELETE,
    "stripe.customer.tax_id.list": CUSTOMER_TAX_ID_LIST,
}
