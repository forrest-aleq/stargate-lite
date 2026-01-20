"""
NetSuite Vendor Bill Capability Schemas.

Reference: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/article_164484956387.html
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ VENDOR BILL CREATE ============

NETSUITE_VENDORBILL_CREATE = CapabilitySchema(
    capability_key="netsuite.vendorbill.create",
    service="netsuite",
    category="payables",
    description="Create a vendor bill in NetSuite",
    description_detailed=(
        "Creates a vendor bill (accounts payable) in NetSuite. "
        "Vendor bills track money owed to suppliers. Each bill has expense lines "
        "with account allocations. Bills can be approved and paid via vendor payments."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="Vendor internal ID (with or without 'ns:' prefix)",
            example="ns:1234",
        ),
        "expense_lines": ParameterSchema(
            type="array",
            required=True,
            description="Expense line items with account_id and amount",
            items_type="object",
            example=[
                {"account_id": "65", "amount": 500.00, "memo": "Office supplies"},
            ],
        ),
        "tran_date": ParameterSchema(
            type="string",
            required=False,
            description="Bill date (YYYY-MM-DD). Defaults to today.",
        ),
        "due_date": ParameterSchema(
            type="string",
            required=False,
            description="Payment due date (YYYY-MM-DD)",
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="Header memo",
        ),
        "terms": ParameterSchema(
            type="string",
            required=False,
            description="Payment terms internal ID",
        ),
        "ref_number": ParameterSchema(
            type="string",
            required=False,
            description="Vendor's invoice/reference number",
        ),
    },
    returns={
        "bill_id": ReturnFieldSchema(
            type="string",
            description="NetSuite internal ID prefixed with 'ns:'",
        ),
        "tran_id": ReturnFieldSchema(
            type="string",
            description="Transaction number",
        ),
        "amount": ReturnFieldSchema(
            type="number",
            description="Bill total amount",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Bill status (pendingApproval, open, etc.)",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid vendor_id or missing required fields",
            recovery_hint="Verify vendor exists using netsuite.vendor.search",
        ),
        ErrorHint(
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            description="INVALID_KEY_OR_REF - Invalid account ID in expense lines",
            recovery_hint="Verify account IDs exist using netsuite.account.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendor.search", "netsuite.vendor.create"],
        typically_followed_by=["netsuite.vendorbill.approve", "netsuite.payment.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ VENDOR BILL GET ============

NETSUITE_VENDORBILL_GET = CapabilitySchema(
    capability_key="netsuite.vendorbill.get",
    service="netsuite",
    category="payables",
    description="Get a vendor bill by ID",
    description_detailed=(
        "Retrieves a vendor bill from NetSuite by its internal ID. "
        "Returns full details including expense lines, payment status, "
        "and approval status."
    ),
    parameters={
        "bill_id": ParameterSchema(
            type="string",
            required=True,
            description="Vendor bill internal ID (with or without 'ns:' prefix)",
            example="ns:5678",
        ),
    },
    returns={
        "bill_id": ReturnFieldSchema(
            type="string",
            description="NetSuite internal ID prefixed with 'ns:'",
        ),
        "tran_id": ReturnFieldSchema(
            type="string",
            description="Transaction number",
        ),
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="Vendor internal ID",
        ),
        "tran_date": ReturnFieldSchema(
            type="string",
            description="Bill date",
        ),
        "due_date": ReturnFieldSchema(
            type="string",
            description="Payment due date",
        ),
        "amount": ReturnFieldSchema(
            type="number",
            description="Bill total amount",
        ),
        "balance": ReturnFieldSchema(
            type="number",
            description="Amount remaining (unpaid)",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Bill status",
        ),
        "approval_status": ReturnFieldSchema(
            type="string",
            description="Approval workflow status",
        ),
        "expense_lines": ReturnFieldSchema(
            type="array",
            description="Expense line items",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Bill not found",
            recovery_hint="Verify the bill_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendorbill.create", "netsuite.vendorbill.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ VENDOR BILL LIST ============

NETSUITE_VENDORBILL_LIST = CapabilitySchema(
    capability_key="netsuite.vendorbill.list",
    service="netsuite",
    category="payables",
    description="List vendor bills with filters",
    description_detailed=(
        "Lists vendor bills using SuiteQL query. "
        "Supports filtering by vendor, date range, and status. "
        "Returns up to 1000 results per page."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter by vendor internal ID",
        ),
        "from_date": ParameterSchema(
            type="string",
            required=False,
            description="Start date filter (YYYY-MM-DD)",
        ),
        "to_date": ParameterSchema(
            type="string",
            required=False,
            description="End date filter (YYYY-MM-DD)",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max results (default 100, max 1000)",
            default=100,
        ),
    },
    returns={
        "bills": ReturnFieldSchema(
            type="array",
            description="List of vendor bills",
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of bills returned",
        ),
        "has_more": ReturnFieldSchema(
            type="boolean",
            description="Whether more results exist",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid date format or vendor_id",
            recovery_hint="Use YYYY-MM-DD format for dates",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["netsuite.vendorbill.get", "netsuite.vendorbill.approve"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ VENDOR BILL APPROVE ============

NETSUITE_VENDORBILL_APPROVE = CapabilitySchema(
    capability_key="netsuite.vendorbill.approve",
    service="netsuite",
    category="payables",
    description="Approve a vendor bill",
    description_detailed=(
        "Sets the approval status of a vendor bill to Approved. "
        "Only applicable if bill approvals are enabled in NetSuite. "
        "Approved bills can then be scheduled for payment."
    ),
    parameters={
        "bill_id": ParameterSchema(
            type="string",
            required=True,
            description="Vendor bill internal ID (with or without 'ns:' prefix)",
        ),
        "approver_note": ParameterSchema(
            type="string",
            required=False,
            description="Optional approval note/memo",
        ),
    },
    returns={
        "bill_id": ReturnFieldSchema(
            type="string",
            description="Bill internal ID",
        ),
        "approval_status": ReturnFieldSchema(
            type="string",
            description="New approval status ('approved')",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Bill status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Bill not found or already approved",
            recovery_hint="Verify bill exists and is pending approval",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendorbill.list", "netsuite.vendorbill.get"],
        typically_followed_by=["netsuite.payment.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

NETSUITE_VENDORBILL_SCHEMAS: dict[str, CapabilitySchema] = {
    "netsuite.vendorbill.create": NETSUITE_VENDORBILL_CREATE,
    "netsuite.vendorbill.get": NETSUITE_VENDORBILL_GET,
    "netsuite.vendorbill.list": NETSUITE_VENDORBILL_LIST,
    "netsuite.vendorbill.approve": NETSUITE_VENDORBILL_APPROVE,
}

__all__ = ["NETSUITE_VENDORBILL_SCHEMAS"]
