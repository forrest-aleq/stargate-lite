"""
Sage Intacct Accounts Receivable connector.

Reference: https://developer.sage.com/intacct/docs/

Provides:
- AR invoices
- AR payments
- AR aging reports
- Credit memos
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .customers import CustomerMixin

logger = get_logger(__name__)


class ARMixin(CustomerMixin):
    """Mixin providing Accounts Receivable capabilities."""

    def list_ar_invoices(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List AR invoices.

        Args:
            customer_id: Filter by customer
            date_from: Filter from this date (YYYY-MM-DD)
            date_to: Filter to this date (YYYY-MM-DD)
            state: Filter by state - "draft", "submitted", "approved", "posted"
            page_size: Results per page
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("customer_id"):
            filters.append(f'customer.id eq "{args["customer_id"]}"')
        if args.get("date_from"):
            filters.append(f'whenCreated ge "{args["date_from"]}"')
        if args.get("date_to"):
            filters.append(f'whenCreated le "{args["date_to"]}"')
        if args.get("state"):
            filters.append(f'state eq "{args["state"]}"')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        invoices = self._paginate("objects/ar-invoice", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct AR invoices listed",
            service="sage_intacct",
            count=len(invoices),
            log_event="ar_invoices_listed",
        )

        return {
            "invoices": [self._format_ar_invoice(inv) for inv in invoices],
            "count": len(invoices),
            "status": "success",
        }

    def get_ar_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get a specific AR invoice.

        Args:
            invoice_key: Invoice key (required)
        """
        cred = self._get_access_token(org_id, user_id)

        invoice_key = args.get("invoice_key")
        if not invoice_key:
            raise ValidationError("invoice_key", "invoice_key is required")

        result = self._make_api_call("GET", f"objects/ar-invoice/{invoice_key}", cred)
        invoice = result.get("ia::result", {})

        if not invoice:
            return {"invoice": None, "status": "not_found"}

        return {"invoice": self._format_ar_invoice(invoice), "status": "success"}

    def create_ar_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create an AR invoice.

        Args:
            customer_id: Customer ID (required)
            invoice_date: Invoice date YYYY-MM-DD (required)
            due_date: Due date YYYY-MM-DD (required)
            lines: Invoice lines (required)
                - description: Line description
                - amount: Line amount
                - gl_account_no: GL account number
                - department_id: Department ID
                - location_id: Location ID
            invoice_no: Invoice number (auto-generated if not provided)
            reference_no: Reference number
            description: Invoice description
            currency: Currency code
            payment_terms: Payment terms
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("customer_id"):
            raise ValidationError("customer_id", "customer_id is required")
        if not args.get("invoice_date"):
            raise ValidationError("invoice_date", "invoice_date is required")
        if not args.get("due_date"):
            raise ValidationError("due_date", "due_date is required")
        if not args.get("lines"):
            raise ValidationError("lines", "At least one invoice line is required")

        invoice_data: dict[str, Any] = {
            "customer": {"id": args["customer_id"]},
            "invoiceDate": args["invoice_date"],
            "dueDate": args["due_date"],
            "arInvoiceItem": [
                self._format_ar_invoice_line_for_api(line) for line in args["lines"]
            ],
        }

        if args.get("invoice_no"):
            invoice_data["invoiceNo"] = args["invoice_no"]
        if args.get("reference_no"):
            invoice_data["referenceNo"] = args["reference_no"]
        if args.get("description"):
            invoice_data["description"] = args["description"]
        if args.get("currency"):
            invoice_data["currency"] = {"baseCurrency": args["currency"]}
        if args.get("payment_terms"):
            invoice_data["term"] = {"name": args["payment_terms"]}

        result = self._make_api_call("POST", "objects/ar-invoice", cred, data=invoice_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct AR invoice created",
            service="sage_intacct",
            invoice_key=created.get("key"),
            customer_id=args["customer_id"],
            log_event="ar_invoice_created",
        )

        return {"invoice": self._format_ar_invoice(created), "status": "success"}

    def post_ar_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Post a draft AR invoice.

        Args:
            invoice_key: Invoice key (required)
        """
        cred = self._get_access_token(org_id, user_id)

        invoice_key = args.get("invoice_key")
        if not invoice_key:
            raise ValidationError("invoice_key", "invoice_key is required")

        self._make_api_call(
            "PATCH", f"objects/ar-invoice/{invoice_key}", cred,
            data={"state": "posted"}
        )

        logger.info(
            "Sage Intacct AR invoice posted",
            service="sage_intacct",
            invoice_key=invoice_key,
            log_event="ar_invoice_posted",
        )

        return {"invoice_key": invoice_key, "status": "posted"}

    def void_ar_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Void an AR invoice.

        Args:
            invoice_key: Invoice key (required)
        """
        cred = self._get_access_token(org_id, user_id)

        invoice_key = args.get("invoice_key")
        if not invoice_key:
            raise ValidationError("invoice_key", "invoice_key is required")

        self._make_api_call("DELETE", f"objects/ar-invoice/{invoice_key}", cred)

        logger.info(
            "Sage Intacct AR invoice voided",
            service="sage_intacct",
            invoice_key=invoice_key,
            log_event="ar_invoice_voided",
        )

        return {"invoice_key": invoice_key, "status": "voided"}

    def list_ar_payments(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List AR payments (customer payments received).

        Args:
            customer_id: Filter by customer
            date_from: Filter from this date
            date_to: Filter to this date
            page_size: Results per page
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("customer_id"):
            filters.append(f'customer.id eq "{args["customer_id"]}"')
        if args.get("date_from"):
            filters.append(f'receiptDate ge "{args["date_from"]}"')
        if args.get("date_to"):
            filters.append(f'receiptDate le "{args["date_to"]}"')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        payments = self._paginate("objects/ar-payment", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct AR payments listed",
            service="sage_intacct",
            count=len(payments),
            log_event="ar_payments_listed",
        )

        return {
            "payments": [self._format_ar_payment(p) for p in payments],
            "count": len(payments),
            "status": "success",
        }

    def create_ar_payment(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Record an AR payment (customer payment).

        Args:
            customer_id: Customer ID (required)
            receipt_date: Payment date YYYY-MM-DD (required)
            payment_method: Payment method - "check", "creditcard", "cash", "eft"
            bank_account_id: Bank account ID for deposit (required)
            amount: Payment amount (required)
            invoice_applications: List of invoice applications (optional)
                - invoice_key: Invoice to apply payment to
                - amount: Amount to apply
            reference_no: Check number or reference
            description: Payment description
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("customer_id"):
            raise ValidationError("customer_id", "customer_id is required")
        if not args.get("receipt_date"):
            raise ValidationError("receipt_date", "receipt_date is required")
        if not args.get("bank_account_id"):
            raise ValidationError("bank_account_id", "bank_account_id is required")
        if not args.get("amount"):
            raise ValidationError("amount", "amount is required")

        payment_data: dict[str, Any] = {
            "customer": {"id": args["customer_id"]},
            "receiptDate": args["receipt_date"],
            "bankAccount": {"glAccountNo": args["bank_account_id"]},
            "receiptAmount": args["amount"],
        }

        if args.get("payment_method"):
            payment_data["paymentMethod"] = args["payment_method"]
        if args.get("reference_no"):
            payment_data["referenceNo"] = args["reference_no"]
        if args.get("description"):
            payment_data["description"] = args["description"]

        if args.get("invoice_applications"):
            payment_data["arPaymentItem"] = [
                {
                    "arInvoice": {"key": app["invoice_key"]},
                    "amountToPay": app["amount"],
                }
                for app in args["invoice_applications"]
            ]

        result = self._make_api_call("POST", "objects/ar-payment", cred, data=payment_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct AR payment created",
            service="sage_intacct",
            payment_key=created.get("key"),
            customer_id=args["customer_id"],
            amount=args["amount"],
            log_event="ar_payment_created",
        )

        return {"payment": self._format_ar_payment(created), "status": "success"}

    def get_ar_aging(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get AR aging report.

        Args:
            as_of_date: Report date (YYYY-MM-DD, default today)
            customer_id: Filter by customer
            aging_periods: Custom aging buckets (default 30, 60, 90, 120)
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        if args.get("as_of_date"):
            params["asOfDate"] = args["as_of_date"]
        if args.get("customer_id"):
            params["customerId"] = args["customer_id"]

        result = self._make_api_call("GET", "services/ar/aging", cred, params=params)
        data = result.get("ia::result", {})

        aging_records = data.get("agingRecords", [])

        logger.info(
            "Sage Intacct AR aging retrieved",
            service="sage_intacct",
            customer_count=len(aging_records),
            log_event="ar_aging_retrieved",
        )

        return {
            "as_of_date": args.get("as_of_date"),
            "aging": [
                {
                    "customer_id": r.get("customerId"),
                    "customer_name": r.get("customerName"),
                    "current": r.get("current", 0),
                    "days_1_30": r.get("days1to30", 0),
                    "days_31_60": r.get("days31to60", 0),
                    "days_61_90": r.get("days61to90", 0),
                    "days_over_90": r.get("daysOver90", 0),
                    "total": r.get("total", 0),
                }
                for r in aging_records
            ],
            "summary": {
                "total_current": data.get("totalCurrent", 0),
                "total_1_30": data.get("total1to30", 0),
                "total_31_60": data.get("total31to60", 0),
                "total_61_90": data.get("total61to90", 0),
                "total_over_90": data.get("totalOver90", 0),
                "grand_total": data.get("grandTotal", 0),
            },
            "customer_count": len(aging_records),
            "status": "success",
        }

    def create_credit_memo(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create an AR credit memo.

        Args:
            customer_id: Customer ID (required)
            credit_date: Credit memo date YYYY-MM-DD (required)
            lines: Credit memo lines (required)
                - description: Line description
                - amount: Line amount
                - gl_account_no: GL account number
            memo_no: Credit memo number
            description: Credit memo description
            apply_to_invoice_key: Invoice key to apply credit to
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("customer_id"):
            raise ValidationError("customer_id", "customer_id is required")
        if not args.get("credit_date"):
            raise ValidationError("credit_date", "credit_date is required")
        if not args.get("lines"):
            raise ValidationError("lines", "At least one credit memo line is required")

        memo_data: dict[str, Any] = {
            "customer": {"id": args["customer_id"]},
            "whenCreated": args["credit_date"],
            "arAdjustmentItem": [
                {
                    "glAccount": {"accountNo": line.get("gl_account_no")},
                    "amount": line.get("amount"),
                    "memo": line.get("description"),
                }
                for line in args["lines"]
            ],
        }

        if args.get("memo_no"):
            memo_data["adjustmentNo"] = args["memo_no"]
        if args.get("description"):
            memo_data["description"] = args["description"]

        result = self._make_api_call("POST", "objects/ar-adjustment", cred, data=memo_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct credit memo created",
            service="sage_intacct",
            memo_key=created.get("key"),
            customer_id=args["customer_id"],
            log_event="credit_memo_created",
        )

        return {
            "credit_memo": {
                "key": created.get("key"),
                "memo_no": created.get("adjustmentNo"),
                "customer_id": args["customer_id"],
                "date": args["credit_date"],
            },
            "status": "success",
        }

    def _format_ar_invoice(self, invoice: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct AR invoice for API response."""
        lines = invoice.get("arInvoiceItem", [])

        return {
            "key": invoice.get("key"),
            "invoice_no": invoice.get("invoiceNo"),
            "record_no": invoice.get("recordNo"),
            "customer_id": invoice.get("customer", {}).get("id"),
            "customer_name": invoice.get("customer", {}).get("name"),
            "invoice_date": invoice.get("invoiceDate"),
            "due_date": invoice.get("dueDate"),
            "state": invoice.get("state"),
            "total_amount": invoice.get("totalEntered"),
            "total_due": invoice.get("totalDue"),
            "total_paid": invoice.get("totalPaid"),
            "currency": invoice.get("currency", {}).get("baseCurrency"),
            "description": invoice.get("description"),
            "reference_no": invoice.get("referenceNo"),
            "lines": [
                {
                    "key": line.get("key"),
                    "description": line.get("memo"),
                    "amount": line.get("amount"),
                    "gl_account_no": line.get("glAccount", {}).get("accountNo"),
                    "department_id": line.get("department", {}).get("id"),
                    "location_id": line.get("location", {}).get("id"),
                }
                for line in lines
            ],
            "created_date": invoice.get("audit", {}).get("createdDateTime"),
            "modified_date": invoice.get("audit", {}).get("modifiedDateTime"),
        }

    def _format_ar_invoice_line_for_api(self, line: dict[str, Any]) -> dict[str, Any]:
        """Format an AR invoice line for Sage Intacct API request."""
        formatted: dict[str, Any] = {
            "amount": line["amount"],
        }

        if line.get("description"):
            formatted["memo"] = line["description"]
        if line.get("gl_account_no"):
            formatted["glAccount"] = {"accountNo": line["gl_account_no"]}
        if line.get("department_id"):
            formatted["department"] = {"id": line["department_id"]}
        if line.get("location_id"):
            formatted["location"] = {"id": line["location_id"]}

        return formatted

    def _format_ar_payment(self, payment: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct AR payment for API response."""
        return {
            "key": payment.get("key"),
            "record_no": payment.get("recordNo"),
            "customer_id": payment.get("customer", {}).get("id"),
            "customer_name": payment.get("customer", {}).get("name"),
            "receipt_date": payment.get("receiptDate"),
            "amount": payment.get("receiptAmount"),
            "payment_method": payment.get("paymentMethod"),
            "bank_account": payment.get("bankAccount", {}).get("glAccountNo"),
            "reference_no": payment.get("referenceNo"),
            "description": payment.get("description"),
            "state": payment.get("state"),
            "applied_invoices": [
                {
                    "invoice_key": item.get("arInvoice", {}).get("key"),
                    "invoice_no": item.get("arInvoice", {}).get("invoiceNo"),
                    "amount_applied": item.get("amountToPay"),
                }
                for item in payment.get("arPaymentItem", [])
            ],
            "created_date": payment.get("audit", {}).get("createdDateTime"),
        }
