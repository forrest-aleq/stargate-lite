"""Square Customer Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
)

SQUARE_CUSTOMERS_LIST = CapabilitySchema(
    capability_key="square.customers.list",
    service="square",
    category="customers",
    description="List customers from Square",
    parameters={
        "cursor": ParameterSchema(type="string", required=False, description="Pagination cursor"),
        "limit": ParameterSchema(
            type="integer", required=False, description="Maximum customers to return"
        ),
        "sort_field": ParameterSchema(
            type="string",
            required=False,
            enum=["DEFAULT", "CREATED_AT"],
            description="Field to sort by",
        ),
        "sort_order": ParameterSchema(
            type="string", required=False, enum=["ASC", "DESC"], description="Sort order"
        ),
    },
    returns={
        "customers": ReturnFieldSchema(
            type="array",
            description="Customers with id, given_name, family_name, email, phone",
        ),
        "cursor": ReturnFieldSchema(type="string", description="Pagination cursor"),
    },
    idempotent=True,
    has_side_effects=False,
)

SQUARE_CUSTOMERS_CREATE = CapabilitySchema(
    capability_key="square.customers.create",
    service="square",
    category="customers",
    description="Create a customer in Square",
    parameters={
        "idempotency_key": ParameterSchema(
            type="string", required=True, description="Unique key for idempotency"
        ),
        "given_name": ParameterSchema(
            type="string", required=False, description="Customer first name"
        ),
        "family_name": ParameterSchema(
            type="string", required=False, description="Customer last name"
        ),
        "company_name": ParameterSchema(type="string", required=False, description="Company name"),
        "email_address": ParameterSchema(
            type="string", required=False, description="Email address"
        ),
        "phone_number": ParameterSchema(type="string", required=False, description="Phone number"),
        "reference_id": ParameterSchema(
            type="string", required=False, description="External reference ID"
        ),
        "note": ParameterSchema(type="string", required=False, description="Customer note"),
    },
    returns={
        "customer_id": ReturnFieldSchema(type="string", description="Created customer ID"),
    },
    idempotent=True,
    has_side_effects=True,
)

SQUARE_CUSTOMERS_UPDATE = CapabilitySchema(
    capability_key="square.customers.update",
    service="square",
    category="customers",
    description="Update a customer in Square",
    parameters={
        "customer_id": ParameterSchema(
            type="string", required=True, description="Square customer ID"
        ),
        "given_name": ParameterSchema(
            type="string", required=False, description="Customer first name"
        ),
        "family_name": ParameterSchema(
            type="string", required=False, description="Customer last name"
        ),
        "email_address": ParameterSchema(
            type="string", required=False, description="Email address (null to clear)"
        ),
        "phone_number": ParameterSchema(
            type="string", required=False, description="Phone number (null to clear)"
        ),
        "note": ParameterSchema(type="string", required=False, description="Customer note"),
        "version": ParameterSchema(
            type="integer", required=False, description="Current version for optimistic locking"
        ),
    },
    returns={
        "customer_id": ReturnFieldSchema(type="string", description="Updated customer ID"),
        "version": ReturnFieldSchema(type="integer", description="New version"),
    },
    idempotent=True,
    has_side_effects=True,
)

CUSTOMER_SCHEMAS = {
    "square.customers.list": SQUARE_CUSTOMERS_LIST,
    "square.customers.create": SQUARE_CUSTOMERS_CREATE,
    "square.customers.update": SQUARE_CUSTOMERS_UPDATE,
}
