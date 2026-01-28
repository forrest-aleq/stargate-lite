"""
Stripe Account Capability Schemas.

Rich metadata for Connect account management.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ ACCOUNTS ============

ACCOUNT_CREATE = CapabilitySchema(
    capability_key="stripe.account.create",
    service="stripe",
    category="accounts",
    description="Create a Connect account",
    description_detailed=(
        "Creates a new connected account for Stripe Connect. Connected accounts "
        "represent your platform's sellers, service providers, or vendors."
    ),
    parameters={
        "type": ParameterSchema(
            type="string",
            required=True,
            description="Account type",
            enum=["standard", "express", "custom"],
            example="express",
        ),
        "country": ParameterSchema(
            type="string",
            required=False,
            description="Two-letter country code",
            example="US",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Account email",
        ),
        "capabilities": ParameterSchema(
            type="object",
            required=False,
            description="Requested capabilities",
            example={"card_payments": {"requested": True}, "transfers": {"requested": True}},
        ),
        "business_type": ParameterSchema(
            type="string",
            required=False,
            description="Business type",
            enum=["individual", "company", "non_profit", "government_entity"],
        ),
        "business_profile": ParameterSchema(
            type="object",
            required=False,
            description="Business details",
        ),
        "company": ParameterSchema(
            type="object",
            required=False,
            description="Company details (if business)",
        ),
        "individual": ParameterSchema(
            type="object",
            required=False,
            description="Individual details",
        ),
        "tos_acceptance": ParameterSchema(
            type="object",
            required=False,
            description="ToS acceptance",
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
            description="Account ID",
            example="acct_ABC123",
        ),
        "type": ReturnFieldSchema(type="string", description="Account type"),
        "email": ReturnFieldSchema(type="string", description="Email"),
        "capabilities": ReturnFieldSchema(type="object", description="Capabilities"),
        "payouts_enabled": ReturnFieldSchema(type="boolean", description="Can payout"),
        "charges_enabled": ReturnFieldSchema(type="boolean", description="Can charge"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.account_link.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

ACCOUNT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.account.retrieve",
    service="stripe",
    category="accounts",
    description="Retrieve a Connect account",
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Account ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Account ID"),
        "type": ReturnFieldSchema(type="string", description="Type"),
        "email": ReturnFieldSchema(type="string", description="Email"),
        "capabilities": ReturnFieldSchema(type="object", description="Capabilities"),
        "payouts_enabled": ReturnFieldSchema(type="boolean", description="Payouts enabled"),
        "charges_enabled": ReturnFieldSchema(type="boolean", description="Charges enabled"),
        "requirements": ReturnFieldSchema(type="object", description="Requirements"),
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

ACCOUNT_UPDATE = CapabilitySchema(
    capability_key="stripe.account.update",
    service="stripe",
    category="accounts",
    description="Update a Connect account",
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Account ID to update",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="New email",
        ),
        "business_profile": ParameterSchema(
            type="object",
            required=False,
            description="Update business info",
        ),
        "company": ParameterSchema(
            type="object",
            required=False,
            description="Update company info",
        ),
        "individual": ParameterSchema(
            type="object",
            required=False,
            description="Update individual info",
        ),
        "capabilities": ParameterSchema(
            type="object",
            required=False,
            description="Request/remove capabilities",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Account ID"),
        "email": ReturnFieldSchema(type="string", description="Updated email"),
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

ACCOUNT_DELETE = CapabilitySchema(
    capability_key="stripe.account.delete",
    service="stripe",
    category="accounts",
    description="Delete a Connect account",
    description_detailed=(
        "Deletes a connected account. Only Custom or Express accounts "
        "created by your platform can be deleted."
    ),
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Account ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted account ID"),
        "deleted": ReturnFieldSchema(type="boolean", description="True if deleted"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Cannot delete Standard accounts",
            recovery_hint="Only Custom/Express accounts can be deleted",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

ACCOUNT_LIST = CapabilitySchema(
    capability_key="stripe.account.list",
    service="stripe",
    category="accounts",
    description="List Connect accounts",
    parameters={
        "created": ParameterSchema(
            type="object",
            required=False,
            description="Filter by created date",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of accounts"),
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

# ============ ACCOUNT LINKS ============

ACCOUNT_LINK_CREATE = CapabilitySchema(
    capability_key="stripe.account_link.create",
    service="stripe",
    category="accounts",
    description="Create an account link",
    description_detailed=(
        "Creates an account link for onboarding a connected account. "
        "Links redirect users to Stripe-hosted onboarding pages."
    ),
    parameters={
        "account": ParameterSchema(
            type="string",
            required=True,
            description="Connected account ID",
        ),
        "type": ParameterSchema(
            type="string",
            required=True,
            description="Link type",
            enum=["account_onboarding", "account_update"],
        ),
        "refresh_url": ParameterSchema(
            type="string",
            required=True,
            description="URL if link expires or fails",
        ),
        "return_url": ParameterSchema(
            type="string",
            required=True,
            description="URL after onboarding completes",
        ),
        "collect": ParameterSchema(
            type="string",
            required=False,
            description="Info to collect",
            enum=["currently_due", "eventually_due"],
        ),
    },
    returns={
        "url": ReturnFieldSchema(type="string", description="Onboarding URL"),
        "expires_at": ReturnFieldSchema(type="integer", description="Link expiration"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Account not found or invalid type",
            recovery_hint="Verify account exists and type is valid",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.account.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ LOGIN LINKS ============

LOGIN_LINK_CREATE = CapabilitySchema(
    capability_key="stripe.account.login_link.create",
    service="stripe",
    category="accounts",
    description="Create a login link for Express Dashboard",
    description_detailed=(
        "Creates a single-use login link for an Express connected account "
        "to access their Stripe Express Dashboard."
    ),
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Express account ID",
        ),
    },
    returns={
        "url": ReturnFieldSchema(type="string", description="Login URL"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Not an Express account",
            recovery_hint="Login links only work for Express accounts",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

# ============ APPLICATION FEES ============

APPLICATION_FEE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.application_fee.retrieve",
    service="stripe",
    category="accounts",
    description="Retrieve an application fee",
    description_detailed=(
        "Retrieves an application fee collected on a payment from a connected account."
    ),
    parameters={
        "fee_id": ParameterSchema(
            type="string",
            required=True,
            description="Application fee ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Fee ID"),
        "amount": ReturnFieldSchema(type="integer", description="Fee amount"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "charge": ReturnFieldSchema(type="string", description="Charge ID"),
        "account": ReturnFieldSchema(type="string", description="Connected account"),
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

APPLICATION_FEE_LIST = CapabilitySchema(
    capability_key="stripe.application_fee.list",
    service="stripe",
    category="accounts",
    description="List application fees",
    parameters={
        "charge": ParameterSchema(
            type="string",
            required=False,
            description="Filter by charge ID",
        ),
        "created": ParameterSchema(
            type="object",
            required=False,
            description="Filter by created date",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of fees"),
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

APPLICATION_FEE_REFUND_CREATE = CapabilitySchema(
    capability_key="stripe.application_fee_refund.create",
    service="stripe",
    category="accounts",
    description="Refund an application fee",
    parameters={
        "fee_id": ParameterSchema(
            type="string",
            required=True,
            description="Application fee ID",
        ),
        "amount": ParameterSchema(
            type="integer",
            required=False,
            description="Amount to refund (partial)",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Refund ID"),
        "amount": ReturnFieldSchema(type="integer", description="Refunded amount"),
        "fee": ReturnFieldSchema(type="string", description="Fee ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Fee already fully refunded",
            recovery_hint="Check fee refund balance",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

ACCOUNT_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.account.create": ACCOUNT_CREATE,
    "stripe.account.retrieve": ACCOUNT_RETRIEVE,
    "stripe.account.update": ACCOUNT_UPDATE,
    "stripe.account.delete": ACCOUNT_DELETE,
    "stripe.account.list": ACCOUNT_LIST,
    "stripe.account_link.create": ACCOUNT_LINK_CREATE,
    "stripe.account.login_link.create": LOGIN_LINK_CREATE,
    "stripe.application_fee.retrieve": APPLICATION_FEE_RETRIEVE,
    "stripe.application_fee.list": APPLICATION_FEE_LIST,
    "stripe.application_fee_refund.create": APPLICATION_FEE_REFUND_CREATE,
}
