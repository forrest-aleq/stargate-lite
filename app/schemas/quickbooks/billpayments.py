"""
QuickBooks Bill Payment Capability Schemas.

Rich metadata for bill payment operations enabling AI agents to use these capabilities effectively.
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
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this bill payment in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/billpayment?txnId=999",
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
            description="List of bill payment objects (each includes deep_link URL to QBO)",
            items_type="object",
            example=[
                {
                    "payment_id": "qb:999",
                    "amount": 500.00,
                    "pay_type": "Check",
                    "txn_date": "2025-01-20",
                    "vendor": "Acme Supply Co.",
                    "deep_link": "https://app.qbo.intuit.com/app/billpayment?txnId=999",
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


# All bill payment schemas
BILLPAYMENT_SCHEMAS: dict[str, CapabilitySchema] = {
    "bill.payment.create": BILL_PAYMENT_CREATE,
    "billpayment.list": BILLPAYMENT_LIST,
}
