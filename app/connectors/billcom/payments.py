"""Bill.com payment operations."""

import time
from datetime import datetime
from typing import Any

from app.connectors.billcom.base import BillComBase
from app.errors import ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)


class BillComPaymentsMixin(BillComBase):
    """Payment operations for Bill.com."""

    def create_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a payment in Bill.com."""
        start_time = time.time()

        payment_data: dict[str, Any] = {
            "processDate": args.get("process_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("bill_ids"):
            payment_data["billId"] = args["bill_ids"][0].replace("bc:", "")
        elif args.get("bill_id"):
            payment_data["billId"] = args["bill_id"].replace("bc:", "")
        elif args.get("create_bill") and args.get("vendor_id"):
            payment_data["createBill"] = True
            payment_data["vendorId"] = args["vendor_id"].replace("bc:", "")
            payment_data["amount"] = args["amount"]

        if args.get("funding_account_id"):
            payment_data["fundingAccount"] = {
                "type": args.get("funding_account_type", "BANK_ACCOUNT"),
                "id": args["funding_account_id"],
            }

        if args.get("amount"):
            payment_data["amount"] = args["amount"]

        result = self._api_call("POST", "/payments", org_id, user_id, json_data=payment_data)

        logger.info(
            "Created Bill.com payment",
            service="billcom",
            payment_id=result.get("id"),
            duration_ms=round((time.time() - start_time) * 1000, 2),
            log_event="payment_created",
        )

        return {
            "payment_id": f"bc:{result['id']}",
            "amount": result.get("amount"),
            "status": result.get("status"),
            "single_status": result.get("singleStatus"),
            "disbursement_status": result.get("disbursementStatus"),
            "process_date": result.get("processDate"),
            "vendor_name": result.get("vendorName"),
        }

    def get_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single payment by ID."""
        payment_id = args["payment_id"].replace("bc:", "")
        result = self._api_call("GET", f"/payments/{payment_id}", org_id, user_id)

        return {
            "payment_id": f"bc:{result['id']}",
            "amount": result.get("amount"),
            "status": result.get("status"),
            "single_status": result.get("singleStatus"),
            "disbursement_status": result.get("disbursementStatus"),
            "process_date": result.get("processDate"),
            "vendor_id": f"bc:{result.get('vendorId', '')}",
            "vendor_name": result.get("vendorName"),
            "bill_id": f"bc:{result.get('billId', '')}",
            "funding_account": result.get("fundingAccount"),
            "created_at": result.get("createdTime"),
            "updated_at": result.get("updatedTime"),
        }

    def get_payment_status(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get payment status (alias for get_payment)."""
        return self.get_payment(org_id, user_id, args)

    def list_payments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List payments from Bill.com."""
        params: dict[str, Any] = {"max": min(args.get("page_size", 50), 100)}

        if args.get("page"):
            params["page"] = args["page"]
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("vendor_id"):
            params["vendorId"] = args["vendor_id"].replace("bc:", "")

        result = self._api_call("GET", "/payments", org_id, user_id, params=params)

        return {
            "payments": [
                {
                    "payment_id": f"bc:{p['id']}",
                    "amount": p.get("amount"),
                    "status": p.get("status"),
                    "single_status": p.get("singleStatus"),
                    "process_date": p.get("processDate"),
                    "vendor_id": f"bc:{p.get('vendorId', '')}",
                    "vendor_name": p.get("vendorName"),
                }
                for p in result.get("results", [])
            ],
            "next_page": result.get("nextPage"),
            "prev_page": result.get("prevPage"),
        }

    def cancel_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Cancel a scheduled payment."""
        payment_id = args["payment_id"].replace("bc:", "")
        result = self._api_call("POST", f"/payments/{payment_id}/cancel", org_id, user_id, json_data={})

        logger.info(
            "Cancelled Bill.com payment",
            service="billcom",
            payment_id=payment_id,
            log_event="payment_cancelled",
        )

        return {
            "payment_id": f"bc:{payment_id}",
            "status": result.get("status", "CANCELLED"),
            "cancelled": True,
        }

    def void_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Void a processed payment."""
        payment_id = args["payment_id"].replace("bc:", "")

        void_data: dict[str, Any] = {}
        if args.get("reason"):
            void_data["voidReason"] = args["reason"]

        result = self._api_call(
            "POST", f"/payments/{payment_id}/void", org_id, user_id, json_data=void_data
        )

        logger.info(
            "Voided Bill.com payment",
            service="billcom",
            payment_id=payment_id,
            log_event="payment_voided",
        )

        return {
            "payment_id": f"bc:{payment_id}",
            "status": result.get("status", "VOIDED"),
            "voided": True,
        }

    def create_bulk_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create bulk payments in Bill.com."""
        start_time = time.time()

        payments = args.get("payments", [])
        if not payments:
            raise ValidationError("payments", "At least one payment required")

        payment_data: dict[str, Any] = {
            "processDate": args.get("process_date", datetime.now().strftime("%Y-%m-%d")),
            "payments": [
                {"billId": p["bill_id"].replace("bc:", ""), "amount": p.get("amount")}
                for p in payments
            ],
        }

        if args.get("funding_account_id"):
            payment_data["fundingAccount"] = {
                "type": args.get("funding_account_type", "BANK_ACCOUNT"),
                "id": args["funding_account_id"],
            }

        result = self._api_call("POST", "/payments/bulk", org_id, user_id, json_data=payment_data)

        logger.info(
            "Created Bill.com bulk payment",
            service="billcom",
            payment_count=len(payments),
            duration_ms=round((time.time() - start_time) * 1000, 2),
            log_event="bulk_payment_created",
        )

        return {
            "batch_id": result.get("batchId"),
            "payments": [
                {"payment_id": f"bc:{p['id']}", "amount": p.get("amount"), "status": p.get("status")}
                for p in result.get("payments", [])
            ],
            "total_payments": len(result.get("payments", [])),
            "total_amount": sum(p.get("amount", 0) for p in result.get("payments", [])),
        }

    def list_bank_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List organization's bank accounts for funding payments."""
        params: dict[str, Any] = {"max": min(args.get("page_size", 50), 100)}

        result = self._api_call("GET", "/bankaccounts", org_id, user_id, params=params)

        return {
            "bank_accounts": [
                {
                    "account_id": ba.get("id"),
                    "name": ba.get("name"),
                    "account_number_last4": ba.get("accountNumberLast4"),
                    "routing_number": ba.get("routingNumber"),
                    "status": ba.get("status"),
                    "is_default": ba.get("isDefault"),
                }
                for ba in result.get("results", [])
            ],
            "next_page": result.get("nextPage"),
            "prev_page": result.get("prevPage"),
        }
