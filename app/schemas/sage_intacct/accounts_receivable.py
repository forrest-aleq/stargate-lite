"""Sage Intacct Accounts Receivable Schemas."""

from app.schemas.base import CapabilitySchema, ParameterSchema, ReturnFieldSchema, WorkflowHints

SAGE_CUSTOMERS_LIST = CapabilitySchema(
    capability_key="sage_intacct.customers.list",
    service="sage_intacct",
    category="accounts_receivable",
    description="List customers from Sage Intacct",
    parameters={
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["active", "inactive"],
        ),
        "customer_type": ParameterSchema(
            type="string", required=False, description="Filter by customer type"
        ),
        "page_size": ParameterSchema(
            type="integer", required=False, description="Number of results per page"
        ),
    },
    returns={
        "customers": ReturnFieldSchema(type="array", description="List of customers"),
        "count": ReturnFieldSchema(type="integer", description="Customer count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["sage_intacct.invoices.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SAGE_CUSTOMERS_CREATE = CapabilitySchema(
    capability_key="sage_intacct.customers.create",
    service="sage_intacct",
    category="accounts_receivable",
    description="Create a customer in Sage Intacct",
    parameters={
        "customer_id": ParameterSchema(
            type="string", required=True, description="Unique customer identifier"
        ),
        "name": ParameterSchema(type="string", required=True, description="Customer display name"),
        "email": ParameterSchema(
            type="string", required=False, description="Customer email address"
        ),
        "phone": ParameterSchema(
            type="string", required=False, description="Customer phone number"
        ),
        "payment_terms": ParameterSchema(
            type="string", required=False, description="Payment terms code"
        ),
        "credit_limit": ParameterSchema(
            type="number", required=False, description="Customer credit limit"
        ),
        "billing_address": ParameterSchema(
            type="object", required=False, description="Billing address object"
        ),
        "shipping_address": ParameterSchema(
            type="object", required=False, description="Shipping address object"
        ),
    },
    returns={
        "customer": ReturnFieldSchema(type="object", description="Created customer"),
        "status": ReturnFieldSchema(type="string", description="Should be 'success'"),
    },
    idempotent=False,
    has_side_effects=True,
)

SAGE_INVOICES_LIST = CapabilitySchema(
    capability_key="sage_intacct.invoices.list",
    service="sage_intacct",
    category="accounts_receivable",
    description="List AR invoices from Sage Intacct",
    parameters={
        "customer_id": ParameterSchema(
            type="string", required=False, description="Filter by customer ID"
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by invoice status",
            enum=["open", "paid", "partialPaid"],
        ),
        "date_from": ParameterSchema(
            type="string", required=False, description="Start date filter (YYYY-MM-DD)"
        ),
        "date_to": ParameterSchema(
            type="string", required=False, description="End date filter (YYYY-MM-DD)"
        ),
        "page_size": ParameterSchema(
            type="integer", required=False, description="Number of results per page"
        ),
    },
    returns={
        "invoices": ReturnFieldSchema(type="array", description="AR invoices"),
        "count": ReturnFieldSchema(type="integer", description="Invoice count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["sage_intacct.ar_payments.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SAGE_INVOICES_CREATE = CapabilitySchema(
    capability_key="sage_intacct.invoices.create",
    service="sage_intacct",
    category="accounts_receivable",
    description="Create an AR invoice in Sage Intacct",
    parameters={
        "customer_id": ParameterSchema(
            type="string", required=True, description="Customer ID for the invoice"
        ),
        "invoice_date": ParameterSchema(
            type="string", required=True, description="Invoice date (YYYY-MM-DD)"
        ),
        "due_date": ParameterSchema(
            type="string", required=False, description="Due date (YYYY-MM-DD)"
        ),
        "lines": ParameterSchema(type="array", required=True, description="Invoice lines"),
        "description": ParameterSchema(
            type="string", required=False, description="Invoice description or memo"
        ),
    },
    returns={
        "invoice": ReturnFieldSchema(type="object", description="Created invoice"),
        "status": ReturnFieldSchema(type="string", description="Should be 'success'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sage_intacct.customers.list"],
        typically_followed_by=["sage_intacct.invoices.post"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SAGE_AR_PAYMENTS_CREATE = CapabilitySchema(
    capability_key="sage_intacct.ar_payments.create",
    service="sage_intacct",
    category="accounts_receivable",
    description="Record an AR payment in Sage Intacct",
    parameters={
        "customer_id": ParameterSchema(
            type="string", required=True, description="Customer ID for the payment"
        ),
        "bank_account_id": ParameterSchema(
            type="string", required=True, description="Bank account ID for deposit"
        ),
        "payment_date": ParameterSchema(
            type="string", required=True, description="Payment date (YYYY-MM-DD)"
        ),
        "invoices": ParameterSchema(
            type="array",
            required=True,
            description="Invoices to apply with invoice_key and amount",
        ),
        "payment_method": ParameterSchema(
            type="string", required=False, description="Payment method (check, ACH, wire)"
        ),
        "reference_number": ParameterSchema(
            type="string", required=False, description="Check or reference number"
        ),
    },
    returns={
        "payment": ReturnFieldSchema(type="object", description="Created payment"),
        "status": ReturnFieldSchema(type="string", description="Should be 'success'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sage_intacct.invoices.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

AR_SCHEMAS = {
    "sage_intacct.customers.list": SAGE_CUSTOMERS_LIST,
    "sage_intacct.customers.create": SAGE_CUSTOMERS_CREATE,
    "sage_intacct.invoices.list": SAGE_INVOICES_LIST,
    "sage_intacct.invoices.create": SAGE_INVOICES_CREATE,
    "sage_intacct.ar_payments.create": SAGE_AR_PAYMENTS_CREATE,
}
