"""Shopify Customer Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
)

SHOPIFY_CUSTOMERS_LIST = CapabilitySchema(
    capability_key="shopify.customers.list",
    service="shopify",
    category="customers",
    description="List customers from Shopify",
    parameters={
        "created_at_min": ParameterSchema(
            type="string", required=False, description="Filter customers created after this date"
        ),
        "created_at_max": ParameterSchema(
            type="string", required=False, description="Filter customers created before this date"
        ),
        "limit": ParameterSchema(
            type="integer", required=False, description="Maximum customers to return"
        ),
    },
    returns={
        "customers": ReturnFieldSchema(
            type="array",
            description="Customers with id, email, first_name, last_name, orders_count",
        ),
        "count": ReturnFieldSchema(type="integer", description="Customer count"),
    },
    idempotent=True,
    has_side_effects=False,
)

SHOPIFY_CUSTOMER_GET = CapabilitySchema(
    capability_key="shopify.customer.get",
    service="shopify",
    category="customers",
    description="Get customer details from Shopify",
    parameters={
        "customer_id": ParameterSchema(
            type="string", required=True, description="Shopify customer ID"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Customer ID"),
        "email": ReturnFieldSchema(type="string", description="Email"),
        "first_name": ReturnFieldSchema(type="string", description="First name"),
        "last_name": ReturnFieldSchema(type="string", description="Last name"),
        "orders_count": ReturnFieldSchema(type="integer", description="Order count"),
        "total_spent": ReturnFieldSchema(type="string", description="Total spent"),
        "created_at": ReturnFieldSchema(type="string", description="Created date"),
        "addresses": ReturnFieldSchema(type="array", description="Addresses"),
    },
    idempotent=True,
    has_side_effects=False,
)

SHOPIFY_CUSTOMER_CREATE = CapabilitySchema(
    capability_key="shopify.customer.create",
    service="shopify",
    category="customers",
    description="Create a customer in Shopify",
    parameters={
        "first_name": ParameterSchema(
            type="string", required=False, description="Customer first name"
        ),
        "last_name": ParameterSchema(
            type="string", required=False, description="Customer last name"
        ),
        "email": ParameterSchema(type="string", required=True, description="Customer email"),
        "phone": ParameterSchema(
            type="string", required=False, description="Customer phone number"
        ),
        "addresses": ParameterSchema(
            type="array", required=False, description="Customer addresses"
        ),
        "send_email_welcome": ParameterSchema(
            type="boolean", required=False, description="Send welcome email"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Created customer ID"),
        "email": ReturnFieldSchema(type="string", description="Customer email"),
    },
    idempotent=False,
    has_side_effects=True,
)

SHOPIFY_CUSTOMERS_UPDATE = CapabilitySchema(
    capability_key="shopify.customers.update",
    service="shopify",
    category="customers",
    description="Update a customer in Shopify",
    parameters={
        "customer_id": ParameterSchema(
            type="string", required=True, description="Shopify customer ID"
        ),
        "first_name": ParameterSchema(
            type="string", required=False, description="Customer first name"
        ),
        "last_name": ParameterSchema(
            type="string", required=False, description="Customer last name"
        ),
        "email": ParameterSchema(type="string", required=False, description="Customer email"),
        "phone": ParameterSchema(
            type="string", required=False, description="Customer phone number"
        ),
        "tags": ParameterSchema(
            type="string", required=False, description="Comma-separated tags"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Customer ID"),
        "updated_at": ReturnFieldSchema(type="string", description="Update timestamp"),
    },
    idempotent=True,
    has_side_effects=True,
)

CUSTOMER_SCHEMAS = {
    "shopify.customers.list": SHOPIFY_CUSTOMERS_LIST,
    "shopify.customer.get": SHOPIFY_CUSTOMER_GET,
    "shopify.customer.create": SHOPIFY_CUSTOMER_CREATE,
}
