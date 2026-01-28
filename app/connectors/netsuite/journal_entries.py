"""
Journal entry and purchase order operations for NetSuite connector.

REST API Reference:
- Journal Entry: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159886587653.html
"""

from datetime import datetime
from typing import Any

from app.logging_config import get_logger

from .accounting_ops import AccountingMixin

logger = get_logger(__name__)


class JournalEntriesMixin(AccountingMixin):
    """Mixin with journal entry and purchase order operations."""

    def create_journal_entry(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a journal entry in NetSuite.

        CRITICAL: Lines must balance (total debits = total credits).

        Args (via args dict):
            subsidiary_id: Required. Internal ID of the subsidiary.
            lines: Required. List of line items with account_id and debit/credit.
            tran_date: Optional. Transaction date (YYYY-MM-DD). Defaults to today.
            memo: Optional. Header memo.
            doc_number: Optional. Custom document number (tranId).

        Returns:
            journal_entry_id, tran_id, tran_date, status
        """
        logger.info(
            "Creating journal entry",
            service="netsuite",
            subsidiary_id=args.get("subsidiary_id"),
            line_count=len(args.get("lines", [])),
            log_event="netsuite_je_create",
        )
        cred = self._get_credentials(org_id, user_id)

        raw_lines = args.get("lines", [])
        if not raw_lines:
            raise ValueError("Journal entry requires at least one line")

        formatted_lines, total_debit, total_credit = self._format_je_lines(raw_lines)
        self._validate_je_balance(total_debit, total_credit)

        journal_data = self._build_je_payload(args, formatted_lines)
        result = self._make_request("POST", "record/v1/journalentry", cred, journal_data)

        logger.info(
            "Journal entry created",
            service="netsuite",
            journal_entry_id=result.get("id"),
            tran_id=result.get("tranId"),
            log_event="netsuite_je_created",
        )

        return {
            "journal_entry_id": f"ns:{result.get('id')}",
            "tran_id": result.get("tranId"),
            "tran_date": result.get("tranDate"),
            "status": "posted",
        }

    def _format_je_lines(
        self, raw_lines: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], float, float]:
        """Format journal entry lines for NetSuite REST API."""
        formatted_lines = []
        total_debit = 0.0
        total_credit = 0.0

        for line in raw_lines:
            formatted_line: dict[str, Any] = {
                "account": {"id": str(line.get("account_id"))},
            }

            if line.get("debit"):
                formatted_line["debit"] = float(line["debit"])
                total_debit += float(line["debit"])
            elif line.get("credit"):
                formatted_line["credit"] = float(line["credit"])
                total_credit += float(line["credit"])
            else:
                raise ValueError("Each line must have either 'debit' or 'credit'")

            if line.get("memo"):
                formatted_line["memo"] = line["memo"]
            if line.get("department_id"):
                formatted_line["department"] = {"id": str(line["department_id"])}
            if line.get("class_id"):
                formatted_line["class"] = {"id": str(line["class_id"])}
            if line.get("location_id"):
                formatted_line["location"] = {"id": str(line["location_id"])}

            formatted_lines.append(formatted_line)

        return formatted_lines, total_debit, total_credit

    def _validate_je_balance(self, total_debit: float, total_credit: float) -> None:
        """Validate that debits equal credits within rounding tolerance."""
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(
                f"Journal entry does not balance. Debits: {total_debit}, Credits: {total_credit}"
            )

    def _build_je_payload(
        self, args: dict[str, Any], formatted_lines: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build the journal entry payload for NetSuite REST API."""
        journal_data: dict[str, Any] = {
            "subsidiary": {"id": str(args.get("subsidiary_id"))},
            "tranDate": args.get("tran_date", datetime.now().strftime("%Y-%m-%d")),
            "line": {"items": formatted_lines},
        }

        if args.get("memo"):
            journal_data["memo"] = args["memo"]
        if args.get("doc_number"):
            journal_data["tranId"] = args["doc_number"]

        return journal_data

    def get_journal_entry(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get a journal entry by ID.

        Args:
            journal_entry_id: NetSuite internal ID (with or without 'ns:' prefix)

        Returns:
            Full journal entry details including lines
        """
        cred = self._get_credentials(org_id, user_id)

        je_id = str(args.get("journal_entry_id", "")).replace("ns:", "")
        if not je_id:
            raise ValueError("journal_entry_id is required")

        result = self._make_request(
            "GET",
            f"record/v1/journalentry/{je_id}",
            cred,
            params={"expandSubResources": "true"},
        )

        return {
            "journal_entry_id": f"ns:{result.get('id')}",
            "tran_id": result.get("tranId"),
            "tran_date": result.get("tranDate"),
            "memo": result.get("memo"),
            "subsidiary_id": result.get("subsidiary", {}).get("id"),
            "lines": result.get("line", {}).get("items", []),
            "status": result.get("approvalStatus", "posted"),
        }

    def create_purchase_order(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a purchase order in NetSuite."""
        logger.info(
            "Creating purchase order",
            service="netsuite",
            vendor_id=args.get("vendor_id"),
            log_event="netsuite_po_create",
        )
        cred = self._get_credentials(org_id, user_id)

        vendor_id = str(args.get("vendor_id", "")).replace("ns:", "")

        raw_items = args.get("item_lines", [])
        formatted_items = self._format_po_items(raw_items)

        po_data: dict[str, Any] = {
            "entity": {"id": vendor_id},
            "tranDate": args.get("tran_date", datetime.now().strftime("%Y-%m-%d")),
            "item": {"items": formatted_items},
        }

        if args.get("memo"):
            po_data["memo"] = args["memo"]
        if args.get("location"):
            po_data["location"] = {"id": str(args["location"])}

        result = self._make_request("POST", "record/v1/purchaseorder", cred, po_data)

        logger.info(
            "Purchase order created",
            service="netsuite",
            po_id=result.get("id"),
            total=result.get("total"),
            log_event="netsuite_po_created",
        )

        return {
            "purchase_order_id": f"ns:{result.get('id')}",
            "tran_id": result.get("tranId"),
            "total": result.get("total"),
            "status": result.get("status"),
        }

    def _format_po_items(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format purchase order item lines for NetSuite REST API."""
        formatted_items = []
        for item in raw_items:
            formatted_item: dict[str, Any] = {
                "item": {"id": str(item.get("item_id"))},
                "quantity": float(item.get("quantity", 1)),
            }
            if item.get("rate"):
                formatted_item["rate"] = float(item["rate"])
            if item.get("description"):
                formatted_item["description"] = item["description"]
            formatted_items.append(formatted_item)
        return formatted_items
