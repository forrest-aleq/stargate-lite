"""
QuickBooks Bill Capability Schemas.

Rich metadata for bill operations enabling AI agents to use these capabilities effectively.
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

BILL_CREATE = CapabilitySchema(
    capability_key="bill.create",
    service="quickbooks",
    category="bills",
    description="Create a bill in QuickBooks",
    description_detailed=(
        "Creates a new bill (accounts payable) in QuickBooks. A bill represents money "
        "owed to a vendor for goods or services received. You must have a valid vendor_id "
        "(use vendor.search or vendor.create first). Line items specify what was purchased "
        "and can be linked to expense accounts or items."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="QuickBooks vendor ID (with 'qb:' prefix)",
            example="qb:123",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Array of line items with Amount and detail (AccountRef or ItemRef)",
            items_type="object",
            example=[
                {
                    "Amount": 500.00,
                    "DetailType": "AccountBasedExpenseLineDetail",
                    "AccountBasedExpenseLineDetail": {
                        "AccountRef": {"value": "7"},
                        "Description": "Office supplies",
                    },
                }
            ],
        ),
        "due_date": ParameterSchema(
            type="string",
            required=False,
            description="Payment due date in YYYY-MM-DD format",
            example="2025-02-15",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Transaction date in YYYY-MM-DD format (defaults to today)",
            example="2025-01-15",
        ),
    },
    returns={
        "bill_id": ReturnFieldSchema(
            type="string",
            description="QuickBooks bill ID with 'qb:' prefix",
            example="qb:456",
        ),
        "doc_number": ReturnFieldSchema(
            type="string",
            description="QuickBooks document/reference number",
            example="1001",
        ),
        "total_amount": ReturnFieldSchema(
            type="number",
            description="Total bill amount",
            example=500.00,
        ),
        "due_date": ReturnFieldSchema(
            type="string",
            description="Payment due date",
            example="2025-02-15",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Bill status ('open' for new bills)",
            example="open",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid vendor_id, missing line items, or invalid account reference",
            recovery_hint=(
                "Verify vendor exists with vendor.get, and account references are valid "
                "using chartofaccounts.get"
            ),
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["vendor.search", "vendor.create", "chartofaccounts.get"],
        typically_followed_by=["bill.get", "bill.payment.create"],
        related_capabilities=["bill.list", "bill.get", "vendor.get"],
    ),
    examples=[
        UsageExample(
            description="Create a bill for office supplies",
            args={
                "vendor_id": "qb:123",
                "line_items": [
                    {
                        "Amount": 250.00,
                        "DetailType": "AccountBasedExpenseLineDetail",
                        "AccountBasedExpenseLineDetail": {
                            "AccountRef": {"value": "7"},
                            "Description": "Printer paper and ink",
                        },
                    }
                ],
                "due_date": "2025-02-01",
            },
            expected_output={
                "bill_id": "qb:789",
                "doc_number": "1002",
                "total_amount": 250.00,
                "due_date": "2025-02-01",
                "status": "open",
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

BILL_GET = CapabilitySchema(
    capability_key="bill.get",
    service="quickbooks",
    category="bills",
    description="Get bill details including line items",
    description_detailed=(
        "Retrieves detailed information about a specific bill including its line items, "
        "current balance, and payment status. Use this to check if a bill has been "
        "partially or fully paid."
    ),
    parameters={
        "bill_id": ParameterSchema(
            type="string",
            required=True,
            description="QuickBooks bill ID (with 'qb:' prefix)",
            example="qb:456",
        ),
    },
    returns={
        "bill_id": ReturnFieldSchema(
            type="string",
            description="QuickBooks bill ID with 'qb:' prefix",
            example="qb:456",
        ),
        "doc_number": ReturnFieldSchema(
            type="string",
            description="QuickBooks document/reference number",
            example="1001",
        ),
        "total_amount": ReturnFieldSchema(
            type="number",
            description="Original total bill amount",
            example=500.00,
        ),
        "balance": ReturnFieldSchema(
            type="number",
            description="Remaining unpaid balance (0 if fully paid)",
            example=250.00,
        ),
        "due_date": ReturnFieldSchema(
            type="string",
            description="Payment due date",
            example="2025-02-15",
        ),
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="Vendor ID this bill is from",
            example="qb:123",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Bill not found with given ID",
            recovery_hint="Verify bill_id is correct using bill.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["bill.create", "bill.list"],
        typically_followed_by=["bill.payment.create"],
        related_capabilities=["bill.list", "billpayment.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

BILL_LIST = CapabilitySchema(
    capability_key="bill.list",
    service="quickbooks",
    category="bills",
    description="List bills with optional vendor/date filters",
    description_detailed=(
        "Returns a list of bills from QuickBooks with optional filtering. Use this to "
        "find bills for a specific vendor or to get a list of unpaid bills. Results "
        "are paginated."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter bills by vendor ID (with 'qb:' prefix)",
            example="qb:123",
        ),
        "unpaid_only": ParameterSchema(
            type="boolean",
            required=False,
            description="If true, only return bills with balance > 0",
            default=False,
            example=True,
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of bills to return",
            default=100,
            example=50,
        ),
    },
    returns={
        "bills": ReturnFieldSchema(
            type="array",
            description="List of bill objects",
            items_type="object",
            example=[
                {
                    "bill_id": "qb:456",
                    "doc_number": "1001",
                    "total_amount": 500.00,
                    "balance": 250.00,
                    "due_date": "2025-02-15",
                    "vendor": "Acme Supply Co.",
                }
            ],
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of bills returned",
            example=10,
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["bill.get", "bill.payment.create"],
        related_capabilities=["bill.get", "billpayment.list", "vendor.list"],
    ),
    examples=[
        UsageExample(
            description="List all unpaid bills for a vendor",
            args={"vendor_id": "qb:123", "unpaid_only": True, "limit": 25},
            expected_output={
                "bills": [
                    {
                        "bill_id": "qb:456",
                        "doc_number": "1001",
                        "total_amount": 500.00,
                        "balance": 500.00,
                        "due_date": "2025-02-15",
                        "vendor": "Acme Supply Co.",
                    }
                ],
                "count": 1,
            },
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

BILL_PAYMENT_CREATE = CapabilitySchema(
    capability_key="bill.payment.create",
    service="quickbooks",
    category="bills",
    description="Create a bill payment in QuickBooks",
    description_detailed=(
        "Records a payment made to a vendor for one or more bills. This creates a "
        "BillPayment transaction in QuickBooks and reduces the balance on the linked "
        "bills. You can pay multiple bills at once by providing multiple bill_ids."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="QuickBooks vendor ID receiving the payment (with 'qb:' prefix)",
            example="qb:123",
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Total payment amount",
            example=500.00,
        ),
        "bill_ids": ParameterSchema(
            type="array",
            required=False,
            description="Array of bill IDs to apply payment to (with 'qb:' prefix)",
            items_type="string",
            example=["qb:456", "qb:789"],
        ),
        "payment_type": ParameterSchema(
            type="string",
            required=False,
            description="Payment method type",
            default="Check",
            enum=["Check", "CreditCard", "Cash"],
            example="Check",
        ),
        "check_num": ParameterSchema(
            type="string",
            required=False,
            description="Check number if payment_type is Check",
            example="1234",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Payment date in YYYY-MM-DD format (defaults to today)",
            example="2025-01-20",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(
            type="string",
            description="QuickBooks bill payment ID with 'qb:' prefix",
            example="qb:999",
        ),
        "amount": ReturnFieldSchema(
            type="number",
            description="Payment amount",
            example=500.00,
        ),
        "pay_type": ReturnFieldSchema(
            type="string",
            description="Payment type used",
            example="Check",
        ),
        "txn_date": ReturnFieldSchema(
            type="string",
            description="Transaction date",
            example="2025-01-20",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid vendor_id, bill_ids, or payment amount exceeds bill balance",
            recovery_hint="Verify vendor and bills exist, and payment amount is valid",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["bill.list", "bill.get"],
        typically_followed_by=["bill.get", "billpayment.list"],
        related_capabilities=["bill.list", "billpayment.list"],
    ),
    examples=[
        UsageExample(
            description="Pay a bill with a check",
            args={
                "vendor_id": "qb:123",
                "amount": 500.00,
                "bill_ids": ["qb:456"],
                "payment_type": "Check",
                "check_num": "5001",
            },
            expected_output={
                "payment_id": "qb:999",
                "amount": 500.00,
                "pay_type": "Check",
                "txn_date": "2025-01-20",
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

BILLPAYMENT_LIST = CapabilitySchema(
    capability_key="billpayment.list",
    service="quickbooks",
    category="bills",
    description="List vendor bill payments with optional filters",
    description_detailed=(
        "Returns a list of bill payments (money paid to vendors) from QuickBooks. "
        "Can be filtered by vendor to see payment history for a specific supplier."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter payments by vendor ID (with 'qb:' prefix)",
            example="qb:123",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of payments to return",
            default=100,
            example=50,
        ),
    },
    returns={
        "payments": ReturnFieldSchema(
            type="array",
            description="List of bill payment objects",
            items_type="object",
            example=[
                {
                    "payment_id": "qb:999",
                    "amount": 500.00,
                    "pay_type": "Check",
                    "txn_date": "2025-01-20",
                    "vendor": "Acme Supply Co.",
                }
            ],
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of payments returned",
            example=5,
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["bill.payment.create"],
        related_capabilities=["bill.list", "bill.payment.create", "vendor.get"],
    ),
    examples=[
        UsageExample(
            description="List recent payments to a vendor",
            args={"vendor_id": "qb:123", "limit": 10},
            expected_output={
                "payments": [
                    {
                        "payment_id": "qb:999",
                        "amount": 500.00,
                        "pay_type": "Check",
                        "txn_date": "2025-01-20",
                        "vendor": "Acme Supply Co.",
                    }
                ],
                "count": 1,
            },
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)


# All bill schemas
BILL_SCHEMAS: dict[str, CapabilitySchema] = {
    "bill.create": BILL_CREATE,
    "bill.get": BILL_GET,
    "bill.list": BILL_LIST,
    "bill.payment.create": BILL_PAYMENT_CREATE,
    "billpayment.list": BILLPAYMENT_LIST,
}
