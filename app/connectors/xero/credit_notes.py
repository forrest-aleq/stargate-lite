"""
Xero Credit Notes connector - Credit note management.

Reference: https://developer.xero.com/documentation/api/accounting/creditnotes

Credit Notes in Xero:
- ACCRECCREDIT: Customer credit notes (reduces AR)
- ACCPAYCREDIT: Supplier credit notes (reduces AP)
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .payments import PaymentsMixin

logger = get_logger(__name__)


class CreditNotesMixin(PaymentsMixin):
    """Mixin providing credit note management capabilities."""

    def list_credit_notes(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List credit notes with optional filtering.

        Args:
            where: Filter expression
            order: Sort field (e.g., "Date DESC")
            page: Page number (1-indexed)
            status: Filter by status - "DRAFT", "SUBMITTED", "AUTHORISED", "PAID", "VOIDED"
            type: "ACCRECCREDIT" (customer) or "ACCPAYCREDIT" (supplier)
            contact_id: Filter by contact
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}
        where_clauses: list[str] = []

        if args.get("where"):
            where_clauses.append(args["where"])

        if args.get("status"):
            where_clauses.append(f'Status=="{args["status"]}"')

        if args.get("type"):
            where_clauses.append(f'Type=="{args["type"]}"')

        if args.get("contact_id"):
            where_clauses.append(f'Contact.ContactID==GUID("{args["contact_id"]}")')

        if where_clauses:
            params["where"] = " AND ".join(where_clauses)

        if args.get("order"):
            params["order"] = args["order"]
        else:
            params["order"] = "Date DESC"

        page = args.get("page", 1)
        params["page"] = page

        result = self._make_api_call("GET", "CreditNotes", cred, tenant_id, params=params)
        credit_notes = result.get("CreditNotes", [])

        logger.info(
            "Xero credit notes listed",
            service="xero",
            count=len(credit_notes),
            page=page,
            log_event="credit_notes_listed",
        )

        return {
            "credit_notes": [self._format_credit_note(cn) for cn in credit_notes],
            "count": len(credit_notes),
            "page": page,
            "status": "success",
        }

    def get_credit_note(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific credit note by ID.

        Args:
            credit_note_id: Xero CreditNoteID (UUID)
            credit_note_number: Alternative - credit note number
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        credit_note_id = args.get("credit_note_id") or args.get("credit_note_number")
        if not credit_note_id:
            raise ValidationError("credit_note_id", "credit_note_id or credit_note_number required")

        result = self._make_api_call("GET", f"CreditNotes/{credit_note_id}", cred, tenant_id)
        credit_notes = result.get("CreditNotes", [])

        if not credit_notes:
            return {"credit_note": None, "status": "not_found"}

        credit_note = credit_notes[0]
        logger.info(
            "Xero credit note retrieved",
            service="xero",
            credit_note_id=credit_note.get("CreditNoteID"),
            log_event="credit_note_retrieved",
        )

        return {"credit_note": self._format_credit_note(credit_note), "status": "success"}

    def create_customer_credit_note(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a customer credit note (reduces AR).

        Args:
            contact_id: Customer ContactID (required)
            line_items: List of line items (required)
            date: Credit note date (YYYY-MM-DD)
            credit_note_number: Your reference number
            reference: Additional reference
            status: DRAFT, SUBMITTED, or AUTHORISED
            line_amount_types: "Exclusive", "Inclusive", or "NoTax"
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("contact_id"):
            raise ValidationError("contact_id", "contact_id is required")
        if not args.get("line_items"):
            raise ValidationError("line_items", "At least one line item is required")

        credit_note_data: dict[str, Any] = {
            "Type": "ACCRECCREDIT",
            "Contact": {"ContactID": args["contact_id"]},
            "LineItems": self._format_line_items_for_credit_note(args["line_items"]),
        }

        if args.get("date"):
            credit_note_data["Date"] = args["date"]
        if args.get("credit_note_number"):
            credit_note_data["CreditNoteNumber"] = args["credit_note_number"]
        if args.get("reference"):
            credit_note_data["Reference"] = args["reference"]
        if args.get("status"):
            credit_note_data["Status"] = args["status"]
        else:
            credit_note_data["Status"] = "DRAFT"
        if args.get("line_amount_types"):
            credit_note_data["LineAmountTypes"] = args["line_amount_types"]

        result = self._make_api_call(
            "POST", "CreditNotes", cred, tenant_id, data={"CreditNotes": [credit_note_data]}
        )

        created = result.get("CreditNotes", [])[0] if result.get("CreditNotes") else {}

        logger.info(
            "Xero customer credit note created",
            service="xero",
            credit_note_id=created.get("CreditNoteID"),
            total=created.get("Total"),
            log_event="customer_credit_note_created",
        )

        return {"credit_note": self._format_credit_note(created), "status": "success"}

    def create_supplier_credit_note(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a supplier credit note (reduces AP).

        Args:
            contact_id: Supplier ContactID (required)
            line_items: List of line items (required)
            date: Credit note date (YYYY-MM-DD)
            credit_note_number: Supplier's credit note number
            reference: Additional reference
            status: DRAFT, SUBMITTED, or AUTHORISED
            line_amount_types: "Exclusive", "Inclusive", or "NoTax"
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("contact_id"):
            raise ValidationError("contact_id", "contact_id is required")
        if not args.get("line_items"):
            raise ValidationError("line_items", "At least one line item is required")

        credit_note_data: dict[str, Any] = {
            "Type": "ACCPAYCREDIT",
            "Contact": {"ContactID": args["contact_id"]},
            "LineItems": self._format_line_items_for_credit_note(args["line_items"]),
        }

        if args.get("date"):
            credit_note_data["Date"] = args["date"]
        if args.get("credit_note_number"):
            credit_note_data["CreditNoteNumber"] = args["credit_note_number"]
        if args.get("reference"):
            credit_note_data["Reference"] = args["reference"]
        if args.get("status"):
            credit_note_data["Status"] = args["status"]
        else:
            credit_note_data["Status"] = "DRAFT"
        if args.get("line_amount_types"):
            credit_note_data["LineAmountTypes"] = args["line_amount_types"]

        result = self._make_api_call(
            "POST", "CreditNotes", cred, tenant_id, data={"CreditNotes": [credit_note_data]}
        )

        created = result.get("CreditNotes", [])[0] if result.get("CreditNotes") else {}

        logger.info(
            "Xero supplier credit note created",
            service="xero",
            credit_note_id=created.get("CreditNoteID"),
            total=created.get("Total"),
            log_event="supplier_credit_note_created",
        )

        return {"credit_note": self._format_credit_note(created), "status": "success"}

    def allocate_credit_note(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Allocate a credit note to one or more invoices.

        Args:
            credit_note_id: CreditNoteID (required)
            allocations: List of allocations
                - invoice_id: Invoice to allocate to
                - amount: Amount to allocate
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        credit_note_id = args.get("credit_note_id")
        if not credit_note_id:
            raise ValidationError("credit_note_id", "credit_note_id is required")

        allocations = args.get("allocations", [])
        if not allocations:
            raise ValidationError("allocations", "At least one allocation is required")

        allocation_data = [
            {"Invoice": {"InvoiceID": a["invoice_id"]}, "Amount": a["amount"]} for a in allocations
        ]

        result = self._make_api_call(
            "PUT",
            f"CreditNotes/{credit_note_id}/Allocations",
            cred,
            tenant_id,
            data={"Allocations": allocation_data},
        )

        created_allocations = result.get("Allocations", [])

        logger.info(
            "Xero credit note allocated",
            service="xero",
            credit_note_id=credit_note_id,
            allocation_count=len(created_allocations),
            log_event="credit_note_allocated",
        )

        return {
            "credit_note_id": credit_note_id,
            "allocations": [
                {
                    "invoice_id": a.get("Invoice", {}).get("InvoiceID"),
                    "amount": a.get("Amount"),
                    "date": a.get("Date"),
                }
                for a in created_allocations
            ],
            "status": "success",
        }

    def void_credit_note(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Void a credit note.

        Args:
            credit_note_id: Xero CreditNoteID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        credit_note_id = args.get("credit_note_id")
        if not credit_note_id:
            raise ValidationError("credit_note_id", "credit_note_id is required")

        credit_note_data = {"CreditNoteID": credit_note_id, "Status": "VOIDED"}

        self._make_api_call(
            "POST",
            f"CreditNotes/{credit_note_id}",
            cred,
            tenant_id,
            data={"CreditNotes": [credit_note_data]},
        )

        logger.info(
            "Xero credit note voided",
            service="xero",
            credit_note_id=credit_note_id,
            log_event="credit_note_voided",
        )

        return {"credit_note_id": credit_note_id, "status": "voided"}

    def _format_credit_note(self, credit_note: dict[str, Any]) -> dict[str, Any]:
        """Format a Xero credit note for API response."""
        contact = credit_note.get("Contact", {})
        line_items = credit_note.get("LineItems", [])
        allocations = credit_note.get("Allocations", [])

        return {
            "credit_note_id": credit_note.get("CreditNoteID"),
            "credit_note_number": credit_note.get("CreditNoteNumber"),
            "type": credit_note.get("Type"),
            "status": credit_note.get("Status"),
            "contact": {
                "contact_id": contact.get("ContactID"),
                "name": contact.get("Name"),
            },
            "date": credit_note.get("Date"),
            "currency_code": credit_note.get("CurrencyCode"),
            "currency_rate": credit_note.get("CurrencyRate"),
            "line_amount_types": credit_note.get("LineAmountTypes"),
            "sub_total": credit_note.get("SubTotal"),
            "total_tax": credit_note.get("TotalTax"),
            "total": credit_note.get("Total"),
            "remaining_credit": credit_note.get("RemainingCredit"),
            "line_items": [
                {
                    "line_item_id": li.get("LineItemID"),
                    "description": li.get("Description"),
                    "quantity": li.get("Quantity"),
                    "unit_amount": li.get("UnitAmount"),
                    "account_code": li.get("AccountCode"),
                    "tax_type": li.get("TaxType"),
                    "tax_amount": li.get("TaxAmount"),
                    "line_amount": li.get("LineAmount"),
                }
                for li in line_items
            ],
            "allocations": [
                {
                    "invoice_id": a.get("Invoice", {}).get("InvoiceID"),
                    "amount": a.get("Amount"),
                    "date": a.get("Date"),
                }
                for a in allocations
            ],
            "has_attachments": credit_note.get("HasAttachments", False),
            "updated_date": credit_note.get("UpdatedDateUTC"),
        }

    def _format_line_items_for_credit_note(
        self, line_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format line items for credit note API request."""
        formatted: list[dict[str, Any]] = []
        for li in line_items:
            xero_li: dict[str, Any] = {}

            if li.get("description"):
                xero_li["Description"] = li["description"]
            if li.get("quantity") is not None:
                xero_li["Quantity"] = li["quantity"]
            else:
                xero_li["Quantity"] = 1
            if li.get("unit_amount") is not None:
                xero_li["UnitAmount"] = li["unit_amount"]
            if li.get("account_code"):
                xero_li["AccountCode"] = li["account_code"]
            if li.get("tax_type"):
                xero_li["TaxType"] = li["tax_type"]

            formatted.append(xero_li)
        return formatted
