"""
Xero Payments connector - Payment management for invoices and bills.

Reference: https://developer.xero.com/documentation/api/accounting/payments

Payments in Xero record money in (for invoices) or money out (for bills).
They are linked to bank accounts and can be allocated to multiple invoices.
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .bills import BillsMixin

logger = get_logger(__name__)


class PaymentsMixin(BillsMixin):
    """Mixin providing payment management capabilities."""

    def list_payments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List payments with optional filtering.

        Args:
            where: Filter expression
            order: Sort field (e.g., "Date DESC")
            page: Page number (1-indexed)
            status: Filter by status - "AUTHORISED" or "DELETED"
            payment_type: "ACCRECPAYMENT" (AR) or "ACCPAYPAYMENT" (AP)
            date_from: Filter payments from this date
            date_to: Filter payments to this date
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}
        where_clauses: list[str] = []

        if args.get("where"):
            where_clauses.append(args["where"])

        if args.get("status"):
            where_clauses.append(f'Status=="{args["status"]}"')

        if args.get("payment_type"):
            where_clauses.append(f'PaymentType=="{args["payment_type"]}"')

        if args.get("date_from"):
            where_clauses.append(f'Date>=DateTime({args["date_from"].replace("-", ",")})')

        if args.get("date_to"):
            where_clauses.append(f'Date<=DateTime({args["date_to"].replace("-", ",")})')

        if where_clauses:
            params["where"] = " AND ".join(where_clauses)

        if args.get("order"):
            params["order"] = args["order"]
        else:
            params["order"] = "Date DESC"

        page = args.get("page", 1)
        params["page"] = page

        result = self._make_api_call("GET", "Payments", cred, tenant_id, params=params)
        payments = result.get("Payments", [])

        logger.info(
            "Xero payments listed",
            service="xero",
            count=len(payments),
            page=page,
            log_event="payments_listed",
        )

        return {
            "payments": [self._format_payment(p) for p in payments],
            "count": len(payments),
            "page": page,
            "status": "success",
        }

    def get_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific payment by ID.

        Args:
            payment_id: Xero PaymentID (UUID)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        payment_id = args.get("payment_id")
        if not payment_id:
            raise ValidationError("payment_id", "payment_id required")

        result = self._make_api_call("GET", f"Payments/{payment_id}", cred, tenant_id)
        payments = result.get("Payments", [])

        if not payments:
            return {"payment": None, "status": "not_found"}

        payment = payments[0]
        logger.info(
            "Xero payment retrieved",
            service="xero",
            payment_id=payment.get("PaymentID"),
            log_event="payment_retrieved",
        )

        return {"payment": self._format_payment(payment), "status": "success"}

    def create_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a payment for an invoice or bill.

        Args:
            invoice_id: InvoiceID to pay (required)
            account_id: Bank account ID (required)
            amount: Payment amount (required)
            date: Payment date (YYYY-MM-DD, default today)
            reference: Payment reference
            is_reconciled: Mark as reconciled (default False)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("invoice_id"):
            raise ValidationError("invoice_id", "invoice_id is required")
        if not args.get("account_id"):
            raise ValidationError("account_id", "account_id (bank account) is required")
        if args.get("amount") is None:
            raise ValidationError("amount", "amount is required")

        payment_data: dict[str, Any] = {
            "Invoice": {"InvoiceID": args["invoice_id"]},
            "Account": {"AccountID": args["account_id"]},
            "Amount": args["amount"],
        }

        if args.get("date"):
            payment_data["Date"] = args["date"]
        if args.get("reference"):
            payment_data["Reference"] = args["reference"]
        if args.get("is_reconciled") is not None:
            payment_data["IsReconciled"] = args["is_reconciled"]

        result = self._make_api_call(
            "POST", "Payments", cred, tenant_id, data={"Payments": [payment_data]}
        )

        created = result.get("Payments", [])[0] if result.get("Payments") else {}

        logger.info(
            "Xero payment created",
            service="xero",
            payment_id=created.get("PaymentID"),
            amount=args["amount"],
            log_event="payment_created",
        )

        return {"payment": self._format_payment(created), "status": "success"}

    def create_bill_payment(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a payment for a bill (AP payment).

        This is a convenience method that calls create_payment with bill_id.

        Args:
            bill_id: Bill ID to pay (required)
            account_id: Bank account ID (required)
            amount: Payment amount (required)
            date: Payment date (YYYY-MM-DD)
            reference: Payment reference
        """
        # Bills use the same invoice ID internally
        args["invoice_id"] = args.get("bill_id")
        if not args.get("invoice_id"):
            raise ValidationError("bill_id", "bill_id is required")

        result = self.create_payment(org_id, user_id, args)

        logger.info(
            "Xero bill payment created",
            service="xero",
            bill_id=args["invoice_id"],
            amount=args.get("amount"),
            log_event="bill_payment_created",
        )

        return result

    def delete_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete (reverse) a payment.

        Note: This only works for unreconciled payments.

        Args:
            payment_id: Xero PaymentID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        payment_id = args.get("payment_id")
        if not payment_id:
            raise ValidationError("payment_id", "payment_id is required")

        payment_data = {"PaymentID": payment_id, "Status": "DELETED"}

        self._make_api_call(
            "POST", f"Payments/{payment_id}", cred, tenant_id, data={"Payments": [payment_data]}
        )

        logger.info(
            "Xero payment deleted",
            service="xero",
            payment_id=payment_id,
            log_event="payment_deleted",
        )

        return {"payment_id": payment_id, "status": "deleted"}

    def get_payment_history(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get history for a payment.

        Args:
            payment_id: Xero PaymentID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        payment_id = args.get("payment_id")
        if not payment_id:
            raise ValidationError("payment_id", "payment_id is required")

        result = self._make_api_call("GET", f"Payments/{payment_id}/History", cred, tenant_id)
        history = result.get("HistoryRecords", [])

        return {
            "payment_id": payment_id,
            "history": [
                {
                    "date": h.get("DateUTC"),
                    "changes": h.get("Changes"),
                    "user": h.get("User"),
                    "details": h.get("Details"),
                }
                for h in history
            ],
            "count": len(history),
            "status": "success",
        }

    def create_batch_payment(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a batch payment for multiple bills.

        This creates payments from a single batch which is useful for payment runs.

        Args:
            account_id: Bank account ID (required)
            date: Payment date (YYYY-MM-DD)
            payments: List of payment details
                - bill_id: Bill ID to pay
                - amount: Payment amount
                - reference: Optional reference
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("account_id"):
            raise ValidationError("account_id", "account_id is required")
        if not args.get("payments"):
            raise ValidationError("payments", "payments list is required")

        payment_date = args.get("date")
        account_id = args["account_id"]

        # Build payment batch
        payments_data: list[dict[str, Any]] = []
        for p in args["payments"]:
            payment_data: dict[str, Any] = {
                "Invoice": {"InvoiceID": p["bill_id"]},
                "Account": {"AccountID": account_id},
                "Amount": p["amount"],
            }
            if payment_date:
                payment_data["Date"] = payment_date
            if p.get("reference"):
                payment_data["Reference"] = p["reference"]

            payments_data.append(payment_data)

        result = self._make_api_call(
            "POST", "Payments", cred, tenant_id, data={"Payments": payments_data}
        )

        created_payments = result.get("Payments", [])
        total_amount = sum(p.get("Amount", 0) for p in created_payments)

        logger.info(
            "Xero batch payment created",
            service="xero",
            payment_count=len(created_payments),
            total_amount=total_amount,
            log_event="batch_payment_created",
        )

        return {
            "payments": [self._format_payment(p) for p in created_payments],
            "count": len(created_payments),
            "total_amount": total_amount,
            "status": "success",
        }

    def _format_payment(self, payment: dict[str, Any]) -> dict[str, Any]:
        """Format a Xero payment for API response."""
        invoice = payment.get("Invoice", {})
        account = payment.get("Account", {})

        return {
            "payment_id": payment.get("PaymentID"),
            "payment_type": payment.get("PaymentType"),
            "status": payment.get("Status"),
            "date": payment.get("Date"),
            "amount": payment.get("Amount"),
            "currency_rate": payment.get("CurrencyRate"),
            "reference": payment.get("Reference"),
            "is_reconciled": payment.get("IsReconciled", False),
            "invoice": {
                "invoice_id": invoice.get("InvoiceID"),
                "invoice_number": invoice.get("InvoiceNumber"),
                "type": invoice.get("Type"),
            },
            "account": {
                "account_id": account.get("AccountID"),
                "code": account.get("Code"),
                "name": account.get("Name"),
            },
            "updated_date": payment.get("UpdatedDateUTC"),
        }
