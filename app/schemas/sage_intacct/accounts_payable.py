"""Sage Intacct Accounts Payable Schemas."""

from app.schemas.base import CapabilitySchema, ParameterSchema, ReturnFieldSchema, WorkflowHints

SAGE_VENDORS_LIST = CapabilitySchema(
    capability_key="sage_intacct.vendors.list",
    service="sage_intacct",
    category="accounts_payable",
    description="List vendors from Sage Intacct",
    parameters={
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["active", "inactive"],
        ),
        "vendor_type": ParameterSchema(
            type="string", required=False, description="Filter by vendor type"
        ),
        "page_size": ParameterSchema(
            type="integer", required=False, description="Number of results per page"
        ),
    },
    returns={
        "vendors": ReturnFieldSchema(type="array", description="List of vendors"),
        "count": ReturnFieldSchema(type="integer", description="Vendor count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["sage_intacct.bills.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SAGE_VENDORS_CREATE = CapabilitySchema(
    capability_key="sage_intacct.vendors.create",
    service="sage_intacct",
    category="accounts_payable",
    description="Create a vendor in Sage Intacct",
    parameters={
        "vendor_id": ParameterSchema(
            type="string", required=True, description="Unique vendor identifier"
        ),
        "name": ParameterSchema(type="string", required=True, description="Vendor display name"),
        "email": ParameterSchema(type="string", required=False, description="Vendor email address"),
        "phone": ParameterSchema(type="string", required=False, description="Vendor phone number"),
        "tax_id": ParameterSchema(
            type="string", required=False, description="Tax identification number"
        ),
        "payment_term": ParameterSchema(
            type="string", required=False, description="Payment terms code"
        ),
        "address": ParameterSchema(
            type="object", required=False, description="Vendor address object"
        ),
    },
    returns={
        "vendor": ReturnFieldSchema(type="object", description="Created vendor"),
        "status": ReturnFieldSchema(type="string", description="Should be 'success'"),
    },
    idempotent=False,
    has_side_effects=True,
)

SAGE_BILLS_LIST = CapabilitySchema(
    capability_key="sage_intacct.bills.list",
    service="sage_intacct",
    category="accounts_payable",
    description="List AP bills from Sage Intacct",
    parameters={
        "vendor_id": ParameterSchema(
            type="string", required=False, description="Filter by vendor ID"
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by bill status",
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
        "bills": ReturnFieldSchema(type="array", description="AP bills"),
        "count": ReturnFieldSchema(type="integer", description="Bill count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["sage_intacct.bill_payments.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SAGE_BILLS_CREATE = CapabilitySchema(
    capability_key="sage_intacct.bills.create",
    service="sage_intacct",
    category="accounts_payable",
    description="Create an AP bill in Sage Intacct",
    parameters={
        "vendor_id": ParameterSchema(
            type="string", required=True, description="Vendor ID for the bill"
        ),
        "bill_date": ParameterSchema(
            type="string", required=True, description="Bill date (YYYY-MM-DD)"
        ),
        "due_date": ParameterSchema(
            type="string", required=False, description="Due date (YYYY-MM-DD)"
        ),
        "bill_number": ParameterSchema(
            type="string", required=False, description="External bill/invoice number"
        ),
        "lines": ParameterSchema(
            type="array",
            required=True,
            description="Bill lines with gl_account, amount, memo",
        ),
        "description": ParameterSchema(
            type="string", required=False, description="Bill description or memo"
        ),
    },
    returns={
        "bill": ReturnFieldSchema(type="object", description="Created bill"),
        "status": ReturnFieldSchema(type="string", description="Should be 'success'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sage_intacct.vendors.list"],
        typically_followed_by=["sage_intacct.bills.post"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SAGE_BILLS_POST = CapabilitySchema(
    capability_key="sage_intacct.bills.post",
    service="sage_intacct",
    category="accounts_payable",
    description="Post a draft AP bill in Sage Intacct",
    parameters={
        "bill_key": ParameterSchema(
            type="string", required=True, description="Sage Intacct bill record key"
        ),
    },
    returns={
        "bill_key": ReturnFieldSchema(type="string", description="Posted bill key"),
        "status": ReturnFieldSchema(type="string", description="Should be 'posted'"),
    },
    idempotent=True,
    has_side_effects=True,
)

SAGE_BILL_PAYMENTS_CREATE = CapabilitySchema(
    capability_key="sage_intacct.bill_payments.create",
    service="sage_intacct",
    category="accounts_payable",
    description="Create a bill payment in Sage Intacct",
    parameters={
        "bank_account_id": ParameterSchema(
            type="string", required=True, description="Bank account ID for payment"
        ),
        "payment_date": ParameterSchema(
            type="string", required=True, description="Payment date (YYYY-MM-DD)"
        ),
        "bills": ParameterSchema(
            type="array",
            required=True,
            description="Bills to pay with bill_key and amount",
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
        typically_preceded_by=["sage_intacct.bills.list", "sage_intacct.bank_accounts.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

AP_SCHEMAS = {
    "sage_intacct.vendors.list": SAGE_VENDORS_LIST,
    "sage_intacct.vendors.create": SAGE_VENDORS_CREATE,
    "sage_intacct.bills.list": SAGE_BILLS_LIST,
    "sage_intacct.bills.create": SAGE_BILLS_CREATE,
    "sage_intacct.bills.post": SAGE_BILLS_POST,
    "sage_intacct.bill_payments.create": SAGE_BILL_PAYMENTS_CREATE,
}
