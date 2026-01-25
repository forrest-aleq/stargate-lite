"""Bill.com bill operations."""

import time
from datetime import datetime
from typing import Any

from app.connectors.billcom.base import BillComBase
from app.errors import ValidationError
from app.logging_config import get_logger

logger = get_logger(__name__)


class BillComBillsMixin(BillComBase):
    """Bill operations for Bill.com."""

    def create_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a bill in Bill.com."""
        start_time = time.time()
        vendor_id = args["vendor_id"].replace("bc:", "")

        bill_data: dict[str, Any] = {
            "vendorId": vendor_id,
            "invoiceNumber": args.get("invoice_number"),
            "invoiceDate": args.get("invoice_date", datetime.now().strftime("%Y-%m-%d")),
            "dueDate": args["due_date"],
            "billLineItems": args.get("line_items", []),
        }

        if args.get("description"):
            bill_data["description"] = args["description"]
        if args.get("amount") and not bill_data["billLineItems"]:
            bill_data["billLineItems"] = [{"amount": args["amount"]}]

        result = self._api_call("POST", "/bills", org_id, user_id, json_data=bill_data)

        logger.info(
            "Created Bill.com bill",
            service="billcom",
            bill_id=result.get("id"),
            duration_ms=round((time.time() - start_time) * 1000, 2),
            log_event="bill_created",
        )

        return {
            "bill_id": f"bc:{result['id']}",
            "invoice_number": result.get("invoiceNumber"),
            "amount": result.get("amount"),
            "status": result.get("status"),
            "payment_status": result.get("paymentStatus"),
            "approval_status": result.get("approvalStatus"),
            "due_date": result.get("dueDate"),
            "vendor_id": f"bc:{vendor_id}",
        }

    def get_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single bill by ID."""
        bill_id = args["bill_id"].replace("bc:", "")
        result = self._api_call("GET", f"/bills/{bill_id}", org_id, user_id)

        return {
            "bill_id": f"bc:{result['id']}",
            "invoice_number": result.get("invoiceNumber"),
            "invoice_date": result.get("invoiceDate"),
            "due_date": result.get("dueDate"),
            "amount": result.get("amount"),
            "amount_due": result.get("amountDue"),
            "status": result.get("status"),
            "payment_status": result.get("paymentStatus"),
            "approval_status": result.get("approvalStatus"),
            "vendor_id": f"bc:{result.get('vendorId', '')}",
            "vendor_name": result.get("vendorName"),
            "description": result.get("description"),
            "line_items": result.get("billLineItems", []),
            "created_at": result.get("createdTime"),
            "updated_at": result.get("updatedTime"),
        }

    def list_bills(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List bills from Bill.com."""
        params: dict[str, Any] = {"max": min(args.get("page_size", 50), 100)}

        if args.get("page"):
            params["page"] = args["page"]
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("payment_status"):
            params["paymentStatus"] = args["payment_status"]
        if args.get("vendor_id"):
            params["vendorId"] = args["vendor_id"].replace("bc:", "")

        result = self._api_call("GET", "/bills", org_id, user_id, params=params)

        return {
            "bills": [
                {
                    "bill_id": f"bc:{b['id']}",
                    "invoice_number": b.get("invoiceNumber"),
                    "vendor_id": f"bc:{b.get('vendorId', '')}",
                    "vendor_name": b.get("vendorName"),
                    "amount": b.get("amount"),
                    "amount_due": b.get("amountDue"),
                    "due_date": b.get("dueDate"),
                    "status": b.get("status"),
                    "payment_status": b.get("paymentStatus"),
                    "approval_status": b.get("approvalStatus"),
                }
                for b in result.get("results", [])
            ],
            "next_page": result.get("nextPage"),
            "prev_page": result.get("prevPage"),
        }

    def update_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a bill in Bill.com."""
        bill_id = args["bill_id"].replace("bc:", "")

        update_data: dict[str, Any] = {}
        if args.get("invoice_number"):
            update_data["invoiceNumber"] = args["invoice_number"]
        if args.get("due_date"):
            update_data["dueDate"] = args["due_date"]
        if args.get("description"):
            update_data["description"] = args["description"]
        if args.get("line_items"):
            update_data["billLineItems"] = args["line_items"]

        if not update_data:
            raise ValidationError("update_data", "No fields provided to update")

        result = self._api_call("PATCH", f"/bills/{bill_id}", org_id, user_id, json_data=update_data)

        return {
            "bill_id": f"bc:{result['id']}",
            "invoice_number": result.get("invoiceNumber"),
            "amount": result.get("amount"),
            "status": result.get("status"),
            "updated": True,
        }

    def approve_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Approve a bill for payment."""
        bill_id = args["bill_id"].replace("bc:", "")

        approval_data: dict[str, Any] = {}
        if args.get("notes"):
            approval_data["approverNotes"] = args["notes"]

        result = self._api_call(
            "POST", f"/bills/{bill_id}/approve", org_id, user_id, json_data=approval_data
        )

        return {
            "bill_id": f"bc:{bill_id}",
            "approval_status": result.get("approvalStatus", "APPROVED"),
            "approved_at": result.get("approvedTime"),
            "approved_by": result.get("approvedBy"),
        }

    def archive_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Archive (soft delete) a bill."""
        bill_id = args["bill_id"].replace("bc:", "")
        result = self._api_call("POST", f"/bills/{bill_id}/archive", org_id, user_id, json_data={})

        return {
            "bill_id": f"bc:{bill_id}",
            "status": result.get("status", "ARCHIVED"),
            "archived": True,
        }

    def record_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Record an external payment against bills."""
        payment_data: dict[str, Any] = {
            "vendorId": args["vendor_id"].replace("bc:", ""),
            "paymentDate": args.get("payment_date", datetime.now().strftime("%Y-%m-%d")),
            "bills": [
                {"billId": bid.replace("bc:", ""), "amount": args.get("amount")}
                for bid in args.get("bill_ids", [])
            ],
        }

        if args.get("reference_number"):
            payment_data["refNumber"] = args["reference_number"]
        if args.get("notes"):
            payment_data["description"] = args["notes"]

        result = self._api_call("POST", "/bills/record-payment", org_id, user_id, json_data=payment_data)

        return {
            "payment_id": f"bc:{result.get('id', '')}",
            "vendor_id": f"bc:{args['vendor_id'].replace('bc:', '')}",
            "amount": result.get("amount"),
            "status": result.get("status", "RECORDED"),
            "recorded": True,
        }
