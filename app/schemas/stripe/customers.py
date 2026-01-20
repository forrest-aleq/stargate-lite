"""
Stripe Customer Capability Schemas.

Rich metadata for customer operations.
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

CUSTOMER_CREATE = CapabilitySchema(
    capability_key="stripe.customer.create",
    service="stripe",
    category="customers",
    description="Create a customer in Stripe",
    description_detailed=(
        "Creates a new customer object in Stripe. Customers allow you to perform "
        "recurring charges, save payment methods, and track payments. Creating a "
        "customer is often the first step before taking payments."
    ),
    parameters={
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Customer's email address",
            example="customer@example.com",
        ),
        "name": ParameterSchema(
            type="string",
            required=False,
            description="Customer's full name",
            example="John Doe",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Customer's phone number",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Internal description for this customer",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your own use",
            example={"user_id": "123", "plan": "premium"},
        ),
        "address": ParameterSchema(
            type="object",
            required=False,
            description="Customer's address",
            example={
                "line1": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94102",
                "country": "US",
            },
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method to attach to customer",
        ),
        "invoice_settings": ParameterSchema(
            type="object",
            required=False,
            description="Invoice settings (default_payment_method, etc.)",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Customer ID",
            example="cus_ABC123",
        ),
        "email": ReturnFieldSchema(type="string", description="Email address"),
        "name": ReturnFieldSchema(type="string", description="Customer name"),
        "created": ReturnFieldSchema(type="integer", description="Unix timestamp"),
        "default_source": ReturnFieldSchema(type="string", description="Default payment source"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid email or payment method",
            recovery_hint="Verify email format and payment method ID",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=[
            "paymentmethod.attach",
            "subscription.create",
            "payment.create",
        ],
        related_capabilities=["stripe.customer.update", "stripe.customer.list"],
    ),
    examples=[
        UsageExample(
            description="Create a customer with email and metadata",
            args={
                "email": "john@example.com",
                "name": "John Doe",
                "metadata": {"user_id": "usr_123"},
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

CUSTOMER_RETRIEVE = CapabilitySchema(
    capability_key="stripe.customer.retrieve",
    service="stripe",
    category="customers",
    description="Retrieve a customer in Stripe",
    description_detailed="Retrieves the details of an existing customer by ID.",
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
            example="cus_ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Customer ID"),
        "email": ReturnFieldSchema(type="string", description="Email address"),
        "name": ReturnFieldSchema(type="string", description="Customer name"),
        "phone": ReturnFieldSchema(type="string", description="Phone number"),
        "address": ReturnFieldSchema(type="object", description="Address object"),
        "metadata": ReturnFieldSchema(type="object", description="Metadata"),
        "default_source": ReturnFieldSchema(type="string", description="Default payment source"),
        "invoice_settings": ReturnFieldSchema(type="object", description="Invoice settings"),
        "created": ReturnFieldSchema(type="integer", description="Unix timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Customer not found",
            recovery_hint="Verify customer_id is correct",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

CUSTOMER_UPDATE = CapabilitySchema(
    capability_key="stripe.customer.update",
    service="stripe",
    category="customers",
    description="Update a customer in Stripe",
    description_detailed="Updates the specified customer by setting parameter values.",
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID to update",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="New email address",
        ),
        "name": ParameterSchema(
            type="string",
            required=False,
            description="New name",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="New phone number",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="New description",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata (merged with existing)",
        ),
        "address": ParameterSchema(
            type="object",
            required=False,
            description="Updated address",
        ),
        "default_source": ParameterSchema(
            type="string",
            required=False,
            description="New default payment source",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Customer ID"),
        "email": ReturnFieldSchema(type="string", description="Updated email"),
        "name": ReturnFieldSchema(type="string", description="Updated name"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Customer not found",
            recovery_hint="Verify customer_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.customer.retrieve"],
    ),
    idempotent=True,
    has_side_effects=True,
)

CUSTOMER_LIST = CapabilitySchema(
    capability_key="stripe.customer.list",
    service="stripe",
    category="customers",
    description="List customers in Stripe",
    description_detailed="Returns a list of customers in reverse chronological order.",
    parameters={
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Filter by email address",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return (1-100)",
            default=10,
        ),
        "starting_after": ParameterSchema(
            type="string",
            required=False,
            description="Cursor for pagination (customer ID)",
        ),
        "ending_before": ParameterSchema(
            type="string",
            required=False,
            description="Cursor for pagination (customer ID)",
        ),
        "created": ParameterSchema(
            type="object",
            required=False,
            description="Filter by created date (gte, lte, gt, lt)",
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of customer objects"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results available"),
        "url": ReturnFieldSchema(type="string", description="API endpoint URL"),
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

CUSTOMER_DELETE = CapabilitySchema(
    capability_key="stripe.customer.delete",
    service="stripe",
    category="customers",
    description="Delete a customer in Stripe",
    description_detailed=(
        "Permanently deletes a customer and cancels any active subscriptions. "
        "This cannot be undone. Also immediately cancels any active subscriptions."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted customer ID"),
        "deleted": ReturnFieldSchema(type="boolean", description="True if deleted"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Customer not found or already deleted",
            recovery_hint="Verify customer_id is correct",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

CUSTOMER_SEARCH = CapabilitySchema(
    capability_key="stripe.customer.search",
    service="stripe",
    category="customers",
    description="Search customers in Stripe",
    description_detailed=(
        "Search for customers using Stripe's Search API. Supports searching by "
        "email, name, phone, metadata, and more using query syntax."
    ),
    parameters={
        "query": ParameterSchema(
            type="string",
            required=True,
            description="Search query string",
            example="email:'john@example.com' OR name~'John'",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return (1-100)",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of matching customers"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results available"),
        "total_count": ReturnFieldSchema(type="integer", description="Total matches"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid search query syntax",
            recovery_hint="Check Stripe Search API query syntax documentation",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.customer.retrieve"],
    ),
    idempotent=True,
    has_side_effects=False,
)

CUSTOMER_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.customer.create": CUSTOMER_CREATE,
    "stripe.customer.retrieve": CUSTOMER_RETRIEVE,
    "stripe.customer.update": CUSTOMER_UPDATE,
    "stripe.customer.list": CUSTOMER_LIST,
    "stripe.customer.delete": CUSTOMER_DELETE,
    "stripe.customer.search": CUSTOMER_SEARCH,
}
