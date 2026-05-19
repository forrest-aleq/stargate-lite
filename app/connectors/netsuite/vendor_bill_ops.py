"""
Vendor bill operations for NetSuite connector.

REST API Reference:
- Vendor Bill: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/article_164484956387.html
"""

from datetime import datetime
from typing import Any

from app.logging_config import get_logger

from .base import NetSuiteBase

logger = get_logger(__name__)


class VendorBillMixin(NetSuiteBase):
    """Mixin with vendor bill operations."""

    def create_vendor_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Create a vendor bill in NetSuite.

        Args (via args dict):
            vendor_id: Required. Internal ID of the vendor.
            expense_lines: Required. List of expense line items.
            tran_date: Optional. Bill date. Defaults to today.
            due_date: Optional. Payment due date.
            memo: Optional. Header memo.
            terms: Optional. Payment terms internal ID.
            ref_number: Optional. Vendor's invoice/reference number.
        """
        logger.info(
            "Creating vendor bill",
            service="netsuite",
            vendor_id=args.get("vendor_id"),
            log_event="netsuite_bill_create",
        )
        cred = self._get_credentials(org_id, user_id)

        vendor_id = str(args.get("vendor_id", "")).replace("ns:", "")
        if not vendor_id:
            raise ValueError("vendor_id is required")

        # Transform expense lines to NetSuite format
        raw_lines = args.get("expense_lines", [])
        formatted_lines = self._format_expense_lines(raw_lines)

        bill_data: dict[str, Any] = {
            "entity": {"id": vendor_id},
            "tranDate": args.get("tran_date", datetime.now().strftime("%Y-%m-%d")),
            "expense": {"items": formatted_lines},
        }

        if args.get("due_date"):
            bill_data["dueDate"] = args["due_date"]
        if args.get("memo"):
            bill_data["memo"] = args["memo"]
        if args.get("terms"):
            bill_data["terms"] = {"id": str(args["terms"])}
        if args.get("ref_number"):
            bill_data["tranId"] = args["ref_number"]

        result = self._make_request("POST", "record/v1/vendorbill", cred, bill_data)

        logger.info(
            "Vendor bill created",
            service="netsuite",
            bill_id=result.get("id"),
            amount=result.get("total"),
            log_event="netsuite_bill_created",
        )

        return {
            "bill_id": f"ns:{result.get('id')}",
            "tran_id": result.get("tranId"),
            "amount": result.get("total"),
            "status": result.get("status", "pendingApproval"),
        }

    def _format_expense_lines(self, raw_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format expense lines for NetSuite REST API."""
        formatted_lines = []
        for line in raw_lines:
            formatted_line: dict[str, Any] = {
                "account": {"id": str(line.get("account_id"))},
                "amount": float(line.get("amount", 0)),
            }
            if line.get("memo"):
                formatted_line["memo"] = line["memo"]
            if line.get("department_id"):
                formatted_line["department"] = {"id": str(line["department_id"])}
            if line.get("class_id"):
                formatted_line["class"] = {"id": str(line["class_id"])}
            formatted_lines.append(formatted_line)
        return formatted_lines

    def get_vendor_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a vendor bill by ID."""
        cred = self._get_credentials(org_id, user_id)

        bill_id = str(args.get("bill_id", "")).replace("ns:", "")
        if not bill_id:
            raise ValueError("bill_id is required")

        result = self._make_request(
            "GET",
            f"record/v1/vendorbill/{bill_id}",
            cred,
            params={"expandSubResources": "true"},
        )

        return {
            "bill_id": f"ns:{result.get('id')}",
            "tran_id": result.get("tranId"),
            "vendor_id": f"ns:{result.get('entity', {}).get('id')}",
            "tran_date": result.get("tranDate"),
            "due_date": result.get("dueDate"),
            "amount": result.get("total"),
            "balance": result.get("amountRemaining"),
            "status": result.get("status"),
            "approval_status": result.get("approvalStatus"),
            "expense_lines": result.get("expense", {}).get("items", []),
        }

    def list_vendor_bills(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        List vendor bills using SuiteQL.

        Args:
            vendor_id: Optional. Filter by vendor.
            from_date: Optional. Start date (YYYY-MM-DD).
            to_date: Optional. End date (YYYY-MM-DD).
            limit: Optional. Max results (default 100, max 1000).
        """
        cred = self._get_credentials(org_id, user_id)

        # Build SuiteQL query
        import re

        conditions = ["recordtype = 'vendorbill'"]

        if args.get("vendor_id"):
            # Validate vendor_id as integer
            vendor_id_int = int(str(args["vendor_id"]).replace("ns:", ""))
            conditions.append(f"entity = {vendor_id_int}")
        if args.get("from_date"):
            # Validate date format
            from_date = str(args["from_date"])
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", from_date):
                raise ValueError("from_date must be in YYYY-MM-DD format")
            conditions.append(f"trandate >= TO_DATE('{from_date}', 'YYYY-MM-DD')")
        if args.get("to_date"):
            # Validate date format
            to_date = str(args["to_date"])
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", to_date):
                raise ValueError("to_date must be in YYYY-MM-DD format")
            conditions.append(f"trandate <= TO_DATE('{to_date}', 'YYYY-MM-DD')")

        where_clause = " AND ".join(conditions)
        # nosec B608: Vendor ID and dates validated before concatenation
        query = f"""
            SELECT id, tranid, trandate, entity, total, status, approvalstatus
            FROM transaction
            WHERE {where_clause}
            ORDER BY trandate DESC
        """

        limit = min(int(args.get("limit", 100)), 1000)
        result = self._make_suiteql_request(cred, query, limit=limit)

        bills = [
            {
                "bill_id": f"ns:{item.get('id')}",
                "tran_id": item.get("tranid"),
                "tran_date": item.get("trandate"),
                "vendor_id": f"ns:{item.get('entity')}",
                "amount": item.get("total"),
                "status": item.get("status"),
                "approval_status": item.get("approvalstatus"),
            }
            for item in result.get("items", [])
        ]

        return {
            "bills": bills,
            "count": len(bills),
            "has_more": result.get("hasMore", False),
        }
