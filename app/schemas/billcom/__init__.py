"""
Bill.com Capability Schemas.

AP automation: vendors, bills, payments, approvals.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ VENDOR CREATE ============

BILLCOM_VENDOR_CREATE = CapabilitySchema(
    capability_key="billcom.vendor.create",
    service="billcom",
    category="ap_automation",
    description="Create a vendor in Bill.com",
    description_detailed=(
        "Creates a new vendor record in Bill.com for payables management. "
        "Vendors can be paid via ACH, wire, or check once created. "
        "Each vendor requires a unique name and payment terms."
    ),
    parameters={
        "vendor_name": ParameterSchema(
            type="string",
            required=True,
            description="Name of the vendor/supplier",
            example="Acme Supplies LLC",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Vendor contact email for payment notifications",
            example="ap@acme-supplies.com",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Vendor phone number",
        ),
        "account_number": ParameterSchema(
            type="string",
            required=False,
            description="Your account number with the vendor",
        ),
        "payment_terms": ParameterSchema(
            type="string",
            required=False,
            description="Payment terms (NET_30, NET_60, DUE_ON_RECEIPT, etc.)",
            default="NET_30",
            enum=["NET_30", "NET_60", "NET_15", "DUE_ON_RECEIPT"],
        ),
        "address": ParameterSchema(
            type="object",
            required=False,
            description="Vendor mailing address",
        ),
    },
    returns={
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="Bill.com vendor ID (prefixed with bc:)",
            example="bc:00901ABC123456789",
        ),
        "vendor_name": ReturnFieldSchema(
            type="string",
            description="Vendor name as stored",
        ),
        "email": ReturnFieldSchema(
            type="string",
            description="Vendor email address",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Vendor status (ACTIVE, INACTIVE)",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Bill.com OAuth credentials not found",
            recovery_hint="Complete Bill.com OAuth flow first",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Vendor name is required",
            recovery_hint="Provide vendor_name parameter",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["billcom.bill.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ VENDOR LIST ============

BILLCOM_VENDOR_LIST = CapabilitySchema(
    capability_key="billcom.vendor.list",
    service="billcom",
    category="ap_automation",
    description="List vendors from Bill.com",
    description_detailed=(
        "Retrieves a paginated list of vendors from Bill.com. "
        "Use to find vendor IDs for creating bills or payments, "
        "or to sync vendor data with your accounting system."
    ),
    parameters={
        "page": ParameterSchema(
            type="integer",
            required=False,
            description="Page number for pagination",
            default=1,
        ),
        "page_size": ParameterSchema(
            type="integer",
            required=False,
            description="Number of vendors per page",
            default=50,
        ),
        "active_only": ParameterSchema(
            type="boolean",
            required=False,
            description="Only return active vendors",
            default=False,
        ),
    },
    returns={
        "vendors": ReturnFieldSchema(
            type="array",
            description="List of vendor records",
        ),
        "total": ReturnFieldSchema(
            type="integer",
            description="Total number of vendors matching criteria",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Bill.com OAuth credentials not found",
            recovery_hint="Complete Bill.com OAuth flow first",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["billcom.bill.create", "billcom.vendor.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ BILL CREATE ============

BILLCOM_BILL_CREATE = CapabilitySchema(
    capability_key="billcom.bill.create",
    service="billcom",
    category="ap_automation",
    description="Create a bill in Bill.com",
    description_detailed=(
        "Creates a new bill (accounts payable) in Bill.com. "
        "Bills track amounts owed to vendors and flow through the approval "
        "workflow before payment. Supports line items for detailed tracking."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="Bill.com vendor ID (with or without bc: prefix)",
            example="bc:00901ABC123456789",
        ),
        "invoice_number": ParameterSchema(
            type="string",
            required=True,
            description="Vendor's invoice number for reference",
            example="INV-2025-001",
        ),
        "invoice_date": ParameterSchema(
            type="string",
            required=True,
            description="Invoice date (YYYY-MM-DD format)",
            example="2025-01-15",
        ),
        "due_date": ParameterSchema(
            type="string",
            required=True,
            description="Payment due date (YYYY-MM-DD format)",
            example="2025-02-14",
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Total bill amount",
            example=1500.00,
        ),
        "line_items": ParameterSchema(
            type="array",
            required=False,
            description="Itemized line items with amounts and GL accounts",
            default=[],
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Bill description or memo",
        ),
    },
    returns={
        "bill_id": ReturnFieldSchema(
            type="string",
            description="Bill.com bill ID (prefixed with bc:)",
            example="bc:00b01XYZ987654321",
        ),
        "invoice_number": ReturnFieldSchema(
            type="string",
            description="Invoice number as stored",
        ),
        "amount": ReturnFieldSchema(
            type="number",
            description="Bill total amount",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Bill status (open, approved, paid)",
        ),
        "due_date": ReturnFieldSchema(
            type="string",
            description="Payment due date",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Missing required fields or invalid vendor_id",
            recovery_hint="Ensure vendor_id, invoice_number, dates, and amount are provided",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["billcom.vendor.list", "billcom.vendor.create"],
        typically_followed_by=["billcom.bill.approve", "billcom.payment.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ BILL LIST ============

BILLCOM_BILL_LIST = CapabilitySchema(
    capability_key="billcom.bill.list",
    service="billcom",
    category="ap_automation",
    description="List bills from Bill.com",
    description_detailed=(
        "Retrieves a paginated list of bills from Bill.com. "
        "Filter by status (OPEN, PAID, SCHEDULED) or vendor. "
        "Use to find bills pending approval or payment."
    ),
    parameters={
        "page": ParameterSchema(
            type="integer",
            required=False,
            description="Page number",
            default=1,
        ),
        "page_size": ParameterSchema(
            type="integer",
            required=False,
            description="Bills per page",
            default=50,
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["OPEN", "PAID", "SCHEDULED"],
        ),
        "vendor_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter by vendor ID",
        ),
    },
    returns={
        "bills": ReturnFieldSchema(
            type="array",
            description="List of bill records with id, amount, status, due_date",
        ),
        "total": ReturnFieldSchema(
            type="integer",
            description="Total bills matching criteria",
        ),
        "page": ReturnFieldSchema(
            type="integer",
            description="Current page number",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Bill.com OAuth credentials not found",
            recovery_hint="Complete Bill.com OAuth flow first",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["billcom.bill.approve", "billcom.payment.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ BILL APPROVE ============

BILLCOM_BILL_APPROVE = CapabilitySchema(
    capability_key="billcom.bill.approve",
    service="billcom",
    category="ap_automation",
    description="Approve a bill in Bill.com",
    description_detailed=(
        "Approves a bill for payment in Bill.com. "
        "Bills typically require approval before they can be paid. "
        "Approval may be part of a multi-step workflow depending on company settings."
    ),
    parameters={
        "bill_id": ParameterSchema(
            type="string",
            required=True,
            description="Bill.com bill ID to approve",
            example="bc:00b01XYZ987654321",
        ),
        "notes": ParameterSchema(
            type="string",
            required=False,
            description="Approver notes or comments",
        ),
    },
    returns={
        "bill_id": ReturnFieldSchema(
            type="string",
            description="Approved bill ID",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="New bill status (APPROVED)",
        ),
        "approved_at": ReturnFieldSchema(
            type="string",
            description="Approval timestamp",
        ),
        "approved_by": ReturnFieldSchema(
            type="string",
            description="Approver user ID or name",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Bill not found or already approved",
            recovery_hint="Verify bill_id is correct and bill is in approvable state",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["billcom.bill.list", "billcom.bill.create"],
        typically_followed_by=["billcom.payment.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ PAYMENT CREATE ============

BILLCOM_PAYMENT_CREATE = CapabilitySchema(
    capability_key="billcom.payment.create",
    service="billcom",
    category="ap_automation",
    description="Create a payment in Bill.com",
    description_detailed=(
        "Creates a payment for one or more approved bills. "
        "Supports ACH (electronic), wire transfer, and check payments. "
        "Payments are scheduled for the specified process date."
    ),
    parameters={
        "bill_ids": ParameterSchema(
            type="array",
            required=True,
            description="List of bill IDs to pay",
            items_type="string",
            example=["bc:00b01XYZ987654321"],
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method",
            default="ACH",
            enum=["ACH", "WIRE", "CHECK"],
        ),
        "process_date": ParameterSchema(
            type="string",
            required=False,
            description="Date to process payment (YYYY-MM-DD), defaults to today",
        ),
        "amount": ParameterSchema(
            type="number",
            required=False,
            description="Payment amount (defaults to bill total)",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(
            type="string",
            description="Bill.com payment ID",
            example="bc:00p01DEF456789012",
        ),
        "amount": ReturnFieldSchema(
            type="number",
            description="Payment amount",
        ),
        "payment_method": ReturnFieldSchema(
            type="string",
            description="Payment method used",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Payment status (SCHEDULED, PROCESSING, COMPLETED)",
        ),
        "process_date": ReturnFieldSchema(
            type="string",
            description="Scheduled process date",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Bills not approved or invalid bill_ids",
            recovery_hint="Ensure all bills are approved before creating payment",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["billcom.bill.approve", "billcom.bill.list"],
        typically_followed_by=["billcom.payment.status"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ PAYMENT BULK ============

BILLCOM_PAYMENT_BULK = CapabilitySchema(
    capability_key="billcom.payment.bulk",
    service="billcom",
    category="ap_automation",
    description="Create bulk payments in Bill.com",
    description_detailed=(
        "Creates multiple payments in a single batch operation. "
        "Useful for weekly or monthly payment runs. "
        "Returns a batch ID for tracking the overall status."
    ),
    parameters={
        "payments": ParameterSchema(
            type="array",
            required=True,
            description="Array of payment objects with bill_ids, amount, payment_method",
            items_type="object",
        ),
    },
    returns={
        "batch_id": ReturnFieldSchema(
            type="string",
            description="Batch ID for tracking the payment run",
        ),
        "total_payments": ReturnFieldSchema(
            type="integer",
            description="Number of payments created",
        ),
        "total_amount": ReturnFieldSchema(
            type="number",
            description="Sum of all payment amounts",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Batch status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="One or more payments failed validation",
            recovery_hint="Check that all bills exist and are approved",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["billcom.bill.list"],
        typically_followed_by=["billcom.payment.status"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ PAYMENT STATUS ============

BILLCOM_PAYMENT_STATUS = CapabilitySchema(
    capability_key="billcom.payment.status",
    service="billcom",
    category="ap_automation",
    description="Get payment status from Bill.com",
    description_detailed=(
        "Retrieves the current status and details of a payment. "
        "Track payment progress from SCHEDULED through PROCESSING to COMPLETED. "
        "Includes vendor information and any error details."
    ),
    parameters={
        "payment_id": ParameterSchema(
            type="string",
            required=True,
            description="Bill.com payment ID to look up",
            example="bc:00p01DEF456789012",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(
            type="string",
            description="Payment ID",
        ),
        "amount": ReturnFieldSchema(
            type="number",
            description="Payment amount",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Current status (SCHEDULED, PROCESSING, COMPLETED, FAILED)",
        ),
        "payment_method": ReturnFieldSchema(
            type="string",
            description="Payment method used",
        ),
        "process_date": ReturnFieldSchema(
            type="string",
            description="Process date",
        ),
        "vendor_name": ReturnFieldSchema(
            type="string",
            description="Vendor receiving payment",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Payment not found",
            recovery_hint="Verify payment_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["billcom.payment.create", "billcom.payment.bulk"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ VENDOR CREDIT CREATE ============

BILLCOM_VENDORCREDIT_CREATE = CapabilitySchema(
    capability_key="billcom.vendorcredit.create",
    service="billcom",
    category="ap_automation",
    description="Create a vendor credit in Bill.com",
    description_detailed=(
        "Creates a vendor credit to track refunds, returns, or adjustments. "
        "Credits can be applied against future bills from the same vendor. "
        "Useful for managing vendor rebates or billing corrections."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="Bill.com vendor ID",
            example="bc:00901ABC123456789",
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Credit amount",
            example=250.00,
        ),
        "credit_date": ParameterSchema(
            type="string",
            required=False,
            description="Credit date (YYYY-MM-DD), defaults to today",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Reason for credit",
            example="Return of damaged goods",
        ),
    },
    returns={
        "credit_id": ReturnFieldSchema(
            type="string",
            description="Vendor credit ID",
            example="bc:00c01GHI789012345",
        ),
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="Vendor ID",
        ),
        "amount": ReturnFieldSchema(
            type="number",
            description="Credit amount",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Credit status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid vendor_id or amount",
            recovery_hint="Verify vendor exists and amount is positive",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["billcom.vendor.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ EXPORT ALL SCHEMAS ============

BILLCOM_SCHEMAS: dict[str, CapabilitySchema] = {
    "billcom.vendor.create": BILLCOM_VENDOR_CREATE,
    "billcom.vendor.list": BILLCOM_VENDOR_LIST,
    "billcom.bill.create": BILLCOM_BILL_CREATE,
    "billcom.bill.list": BILLCOM_BILL_LIST,
    "billcom.bill.approve": BILLCOM_BILL_APPROVE,
    "billcom.payment.create": BILLCOM_PAYMENT_CREATE,
    "billcom.payment.bulk": BILLCOM_PAYMENT_BULK,
    "billcom.payment.status": BILLCOM_PAYMENT_STATUS,
    "billcom.vendorcredit.create": BILLCOM_VENDORCREDIT_CREATE,
}

__all__ = ["BILLCOM_SCHEMAS"]
