"""
NetSuite Payment Capability Schemas.

Vendor payment and purchase order operations.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ VENDOR PAYMENT CREATE ============

NETSUITE_PAYMENT_CREATE = CapabilitySchema(
    capability_key="netsuite.payment.create",
    service="netsuite",
    category="payables",
    description="Create a vendor payment",
    description_detailed=(
        "Creates a vendor payment in NetSuite to pay one or more bills. "
        "Specify the vendor, bank account, and bills to pay. "
        "Payments can be partial or full payment of bills."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="Vendor internal ID (with or without 'ns:' prefix)",
        ),
        "bank_account_id": ParameterSchema(
            type="string",
            required=True,
            description="Bank account internal ID to pay from",
        ),
        "bills_to_pay": ParameterSchema(
            type="array",
            required=False,
            description="Bills to pay with optional amounts",
            items_type="object",
            example=[{"bill_id": "ns:5678", "amount": 500.00}],
        ),
        "payment_date": ParameterSchema(
            type="string",
            required=False,
            description="Payment date (YYYY-MM-DD). Defaults to today.",
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="Payment memo",
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method internal ID (check, ACH, wire, etc.)",
        ),
        "subsidiary_id": ParameterSchema(
            type="string",
            required=False,
            description="Subsidiary internal ID (OneWorld only)",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(
            type="string",
            description="NetSuite payment ID prefixed with 'ns:'",
        ),
        "tran_id": ReturnFieldSchema(
            type="string",
            description="Transaction number",
        ),
        "total": ReturnFieldSchema(
            type="number",
            description="Total payment amount",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Payment status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid vendor, bank account, or bill IDs",
            recovery_hint="Verify all IDs exist before creating payment",
        ),
        ErrorHint(
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            description="Bill already paid or insufficient funds",
            recovery_hint="Check bill status with netsuite.vendorbill.get",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendorbill.approve", "netsuite.vendorbill.list"],
        typically_followed_by=["netsuite.gl.transactions"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ BATCH VENDOR PAYMENTS ============

NETSUITE_PAYMENT_BATCH = CapabilitySchema(
    capability_key="netsuite.payment.batch",
    service="netsuite",
    category="payables",
    description="Process multiple vendor payments",
    description_detailed=(
        "Processes multiple vendor payments in a batch. "
        "Each payment is processed independently - failures don't affect others. "
        "Returns results and errors for each payment."
    ),
    parameters={
        "payments": ParameterSchema(
            type="array",
            required=True,
            description="Array of payment specifications (same format as payment.create)",
            items_type="object",
        ),
    },
    returns={
        "processed": ReturnFieldSchema(
            type="integer",
            description="Number of payments successfully processed",
        ),
        "failed": ReturnFieldSchema(
            type="integer",
            description="Number of payments that failed",
        ),
        "payments": ReturnFieldSchema(
            type="array",
            description="Successful payment results",
        ),
        "errors": ReturnFieldSchema(
            type="array",
            description="Failed payments with error details",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid payment specifications",
            recovery_hint="Ensure each payment has required fields",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendorbill.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ PURCHASE ORDER CREATE ============

NETSUITE_PURCHASEORDER_CREATE = CapabilitySchema(
    capability_key="netsuite.purchaseorder.create",
    service="netsuite",
    category="purchasing",
    description="Create a purchase order",
    description_detailed=(
        "Creates a purchase order in NetSuite. "
        "POs are used to order items from vendors. "
        "When received, POs can be converted to vendor bills."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="Vendor internal ID (with or without 'ns:' prefix)",
        ),
        "item_lines": ParameterSchema(
            type="array",
            required=True,
            description="Item lines with item_id, quantity, and optional rate",
            items_type="object",
            example=[{"item_id": "100", "quantity": 10, "rate": 25.00}],
        ),
        "tran_date": ParameterSchema(
            type="string",
            required=False,
            description="Order date (YYYY-MM-DD). Defaults to today.",
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="PO memo",
        ),
        "location": ParameterSchema(
            type="string",
            required=False,
            description="Location internal ID for receiving",
        ),
    },
    returns={
        "purchase_order_id": ReturnFieldSchema(
            type="string",
            description="NetSuite PO ID prefixed with 'ns:'",
        ),
        "tran_id": ReturnFieldSchema(
            type="string",
            description="Transaction number",
        ),
        "total": ReturnFieldSchema(
            type="number",
            description="PO total amount",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="PO status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid vendor or item IDs",
            recovery_hint="Verify vendor and items exist",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendor.search"],
        typically_followed_by=["netsuite.vendorbill.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

NETSUITE_PAYMENT_SCHEMAS: dict[str, CapabilitySchema] = {
    "netsuite.payment.create": NETSUITE_PAYMENT_CREATE,
    "netsuite.payment.batch": NETSUITE_PAYMENT_BATCH,
    "netsuite.purchaseorder.create": NETSUITE_PURCHASEORDER_CREATE,
}

__all__ = ["NETSUITE_PAYMENT_SCHEMAS"]
