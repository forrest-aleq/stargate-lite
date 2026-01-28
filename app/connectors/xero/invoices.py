"""
Xero Invoices connector - Sales invoice (AR) management.

Reference: https://developer.xero.com/documentation/api/accounting/invoices

Invoice Types:
- ACCREC: Accounts Receivable (sales invoices - customer owes you)
- ACCPAY: Accounts Payable (bills - you owe supplier)

This module handles ACCREC invoices. ACCPAY is handled in bills.py.
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .contacts import ContactsMixin

logger = get_logger(__name__)


class InvoicesMixin(ContactsMixin):
    """Mixin providing sales invoice management capabilities."""

    def list_invoices(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List sales invoices with optional filtering.

        Args:
            where: Filter expression
            order: Sort field (e.g., "Date DESC")
            page: Page number (1-indexed)
            status: Filter by status - "DRAFT", "SUBMITTED", "AUTHORISED", "PAID", "VOIDED"
            contact_id: Filter by customer
            date_from: Filter invoices from this date (YYYY-MM-DD)
            date_to: Filter invoices to this date (YYYY-MM-DD)
            modified_since: Only return invoices modified since this datetime
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}
        where_clauses: list[str] = ['Type=="ACCREC"']  # Only sales invoices

        if args.get("where"):
            where_clauses.append(args["where"])

        if args.get("status"):
            where_clauses.append(f'Status=="{args["status"]}"')

        if args.get("contact_id"):
            where_clauses.append(f'Contact.ContactID==GUID("{args["contact_id"]}")')

        if args.get("date_from"):
            where_clauses.append(f"Date>=DateTime({args['date_from'].replace('-', ',')})")

        if args.get("date_to"):
            where_clauses.append(f"Date<=DateTime({args['date_to'].replace('-', ',')})")

        params["where"] = " AND ".join(where_clauses)

        if args.get("order"):
            params["order"] = args["order"]
        else:
            params["order"] = "Date DESC"

        page = args.get("page", 1)
        params["page"] = page

        if args.get("modified_since"):
            # Use If-Modified-Since header
            pass  # Handled differently - via header

        result = self._make_api_call("GET", "Invoices", cred, tenant_id, params=params)
        invoices = result.get("Invoices", [])

        logger.info(
            "Xero invoices listed",
            service="xero",
            count=len(invoices),
            page=page,
            log_event="invoices_listed",
        )

        return {
            "invoices": [self._format_invoice(inv) for inv in invoices],
            "count": len(invoices),
            "page": page,
            "status": "success",
        }

    def get_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific invoice by ID or number.

        Args:
            invoice_id: Xero InvoiceID (UUID)
            invoice_number: Alternative - invoice number
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        invoice_id = args.get("invoice_id") or args.get("invoice_number")
        if not invoice_id:
            raise ValidationError("invoice_id", "invoice_id or invoice_number required")

        result = self._make_api_call("GET", f"Invoices/{invoice_id}", cred, tenant_id)
        invoices = result.get("Invoices", [])

        if not invoices:
            return {"invoice": None, "status": "not_found"}

        invoice = invoices[0]
        logger.info(
            "Xero invoice retrieved",
            service="xero",
            invoice_id=invoice.get("InvoiceID"),
            log_event="invoice_retrieved",
        )

        return {"invoice": self._format_invoice(invoice), "status": "success"}

    def create_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new sales invoice.

        Args:
            contact_id: Customer ContactID (required)
            line_items: List of line items (required)
                - description: Item description
                - quantity: Quantity (default 1)
                - unit_amount: Unit price
                - account_code: Account code
                - tax_type: Tax type code
                - item_code: Optional inventory item code
                - discount_rate: Optional discount percentage
            date: Invoice date (YYYY-MM-DD, default today)
            due_date: Due date (YYYY-MM-DD)
            invoice_number: Your invoice number (auto-generated if not provided)
            reference: Reference/PO number
            currency_code: Currency code
            status: DRAFT, SUBMITTED, or AUTHORISED
            line_amount_types: "Exclusive", "Inclusive", or "NoTax"
            branding_theme_id: Branding theme UUID
            url: URL for online invoice
            send_to_contact: If true, email invoice to contact
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("contact_id"):
            raise ValidationError("contact_id", "Customer contact_id is required")
        if not args.get("line_items"):
            raise ValidationError("line_items", "At least one line item is required")

        invoice_data: dict[str, Any] = {
            "Type": "ACCREC",  # Sales invoice
            "Contact": {"ContactID": args["contact_id"]},
            "LineItems": self._format_line_items_for_api(args["line_items"]),
        }

        # Optional fields
        if args.get("date"):
            invoice_data["Date"] = args["date"]
        if args.get("due_date"):
            invoice_data["DueDate"] = args["due_date"]
        if args.get("invoice_number"):
            invoice_data["InvoiceNumber"] = args["invoice_number"]
        if args.get("reference"):
            invoice_data["Reference"] = args["reference"]
        if args.get("currency_code"):
            invoice_data["CurrencyCode"] = args["currency_code"]
        if args.get("status"):
            invoice_data["Status"] = args["status"]
        else:
            invoice_data["Status"] = "DRAFT"
        if args.get("line_amount_types"):
            invoice_data["LineAmountTypes"] = args["line_amount_types"]
        if args.get("branding_theme_id"):
            invoice_data["BrandingThemeID"] = args["branding_theme_id"]
        if args.get("url"):
            invoice_data["Url"] = args["url"]

        result = self._make_api_call(
            "POST", "Invoices", cred, tenant_id, data={"Invoices": [invoice_data]}
        )

        created = result.get("Invoices", [])[0] if result.get("Invoices") else {}

        # Send to contact if requested
        if args.get("send_to_contact") and created.get("InvoiceID"):
            self._email_invoice(cred, tenant_id, created["InvoiceID"])

        logger.info(
            "Xero invoice created",
            service="xero",
            invoice_id=created.get("InvoiceID"),
            invoice_number=created.get("InvoiceNumber"),
            total=created.get("Total"),
            log_event="invoice_created",
        )

        return {"invoice": self._format_invoice(created), "status": "success"}

    def update_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an existing invoice (DRAFT or SUBMITTED only).

        Args:
            invoice_id: Xero InvoiceID (required)
            ... (same optional fields as create_invoice)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        invoice_id = args.get("invoice_id")
        if not invoice_id:
            raise ValidationError("invoice_id", "invoice_id is required")

        invoice_data: dict[str, Any] = {"InvoiceID": invoice_id}

        if args.get("contact_id"):
            invoice_data["Contact"] = {"ContactID": args["contact_id"]}
        if args.get("line_items"):
            invoice_data["LineItems"] = self._format_line_items_for_api(args["line_items"])
        if args.get("date"):
            invoice_data["Date"] = args["date"]
        if args.get("due_date"):
            invoice_data["DueDate"] = args["due_date"]
        if args.get("reference"):
            invoice_data["Reference"] = args["reference"]
        if args.get("status"):
            invoice_data["Status"] = args["status"]

        result = self._make_api_call(
            "POST", f"Invoices/{invoice_id}", cred, tenant_id, data={"Invoices": [invoice_data]}
        )

        updated = result.get("Invoices", [])[0] if result.get("Invoices") else {}
        logger.info(
            "Xero invoice updated",
            service="xero",
            invoice_id=invoice_id,
            log_event="invoice_updated",
        )

        return {"invoice": self._format_invoice(updated), "status": "success"}

    def void_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Void an invoice.

        Args:
            invoice_id: Xero InvoiceID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        invoice_id = args.get("invoice_id")
        if not invoice_id:
            raise ValidationError("invoice_id", "invoice_id is required")

        invoice_data = {"InvoiceID": invoice_id, "Status": "VOIDED"}

        self._make_api_call(
            "POST", f"Invoices/{invoice_id}", cred, tenant_id, data={"Invoices": [invoice_data]}
        )

        logger.info(
            "Xero invoice voided",
            service="xero",
            invoice_id=invoice_id,
            log_event="invoice_voided",
        )

        return {"invoice_id": invoice_id, "status": "voided"}

    def email_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Email an invoice to the contact.

        Args:
            invoice_id: Xero InvoiceID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        invoice_id = args.get("invoice_id")
        if not invoice_id:
            raise ValidationError("invoice_id", "invoice_id is required")

        self._email_invoice(cred, tenant_id, invoice_id)

        logger.info(
            "Xero invoice emailed",
            service="xero",
            invoice_id=invoice_id,
            log_event="invoice_emailed",
        )

        return {"invoice_id": invoice_id, "status": "emailed"}

    def _email_invoice(self, cred: dict[str, Any], tenant_id: str, invoice_id: str) -> None:
        """Internal method to email an invoice."""
        self._make_api_call("POST", f"Invoices/{invoice_id}/Email", cred, tenant_id, data={})

    def get_invoice_pdf(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get the PDF URL for an invoice.

        Args:
            invoice_id: Xero InvoiceID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        invoice_id = args.get("invoice_id")
        if not invoice_id:
            raise ValidationError("invoice_id", "invoice_id is required")

        # Get invoice with online URL
        result = self._make_api_call("GET", f"Invoices/{invoice_id}", cred, tenant_id)
        invoice = result.get("Invoices", [{}])[0]

        return {
            "invoice_id": invoice_id,
            "online_invoice_url": invoice.get("OnlineInvoiceUrl"),
            "status": "success",
        }

    def get_outstanding_invoices(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get all outstanding (unpaid) invoices.

        Args:
            contact_id: Optional - filter by customer
            overdue_only: If true, only return overdue invoices
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        where_clauses: list[str] = [
            'Type=="ACCREC"',
            'Status=="AUTHORISED"',
            "AmountDue>0",
        ]

        if args.get("contact_id"):
            where_clauses.append(f'Contact.ContactID==GUID("{args["contact_id"]}")')

        if args.get("overdue_only"):
            # Get invoices where due date has passed
            from datetime import datetime

            today = datetime.utcnow().strftime("%Y,%m,%d")
            where_clauses.append(f"DueDate<DateTime({today})")

        params = {"where": " AND ".join(where_clauses), "order": "DueDate ASC"}

        result = self._make_api_call("GET", "Invoices", cred, tenant_id, params=params)
        invoices = result.get("Invoices", [])

        # Calculate totals
        total_outstanding = sum(inv.get("AmountDue", 0) for inv in invoices)
        total_overdue = sum(
            inv.get("AmountDue", 0)
            for inv in invoices
            if inv.get("HasErrors", False)  # Xero sets this for overdue
        )

        logger.info(
            "Xero outstanding invoices retrieved",
            service="xero",
            count=len(invoices),
            total_outstanding=total_outstanding,
            log_event="outstanding_invoices_retrieved",
        )

        return {
            "invoices": [self._format_invoice(inv) for inv in invoices],
            "count": len(invoices),
            "total_outstanding": total_outstanding,
            "total_overdue": total_overdue,
            "status": "success",
        }

    def get_ar_aging(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get accounts receivable aging summary.

        This calculates aging buckets from outstanding invoices.
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        # Get all outstanding AR invoices
        params = {
            "where": 'Type=="ACCREC" AND Status=="AUTHORISED" AND AmountDue>0',
            "order": "DueDate ASC",
        }

        result = self._make_api_call("GET", "Invoices", cred, tenant_id, params=params)
        invoices = result.get("Invoices", [])

        # Calculate aging buckets
        from datetime import datetime

        today = datetime.utcnow()
        aging: dict[str, dict[str, float]] = {
            "current": {"amount": 0.0, "count": 0},
            "1_30_days": {"amount": 0.0, "count": 0},
            "31_60_days": {"amount": 0.0, "count": 0},
            "61_90_days": {"amount": 0.0, "count": 0},
            "over_90_days": {"amount": 0.0, "count": 0},
        }

        for inv in invoices:
            amount_due = inv.get("AmountDue", 0)
            due_date_str = inv.get("DueDate", "")
            if not due_date_str:
                continue

            # Parse Xero date format
            try:
                due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                days_overdue = (today - due_date.replace(tzinfo=None)).days
            except (ValueError, AttributeError):
                days_overdue = 0

            if days_overdue <= 0:
                aging["current"]["amount"] += amount_due
                aging["current"]["count"] += 1
            elif days_overdue <= 30:
                aging["1_30_days"]["amount"] += amount_due
                aging["1_30_days"]["count"] += 1
            elif days_overdue <= 60:
                aging["31_60_days"]["amount"] += amount_due
                aging["31_60_days"]["count"] += 1
            elif days_overdue <= 90:
                aging["61_90_days"]["amount"] += amount_due
                aging["61_90_days"]["count"] += 1
            else:
                aging["over_90_days"]["amount"] += amount_due
                aging["over_90_days"]["count"] += 1

        total = sum(bucket["amount"] for bucket in aging.values())

        logger.info(
            "Xero AR aging calculated",
            service="xero",
            total_outstanding=total,
            log_event="ar_aging_calculated",
        )

        return {
            "aging": aging,
            "total_outstanding": total,
            "invoice_count": len(invoices),
            "status": "success",
        }

    def _format_invoice(self, invoice: dict[str, Any]) -> dict[str, Any]:
        """Format a Xero invoice for API response."""
        contact = invoice.get("Contact", {})
        line_items = invoice.get("LineItems", [])

        return {
            "invoice_id": invoice.get("InvoiceID"),
            "invoice_number": invoice.get("InvoiceNumber"),
            "type": invoice.get("Type"),
            "status": invoice.get("Status"),
            "contact": {
                "contact_id": contact.get("ContactID"),
                "name": contact.get("Name"),
            },
            "date": invoice.get("Date"),
            "due_date": invoice.get("DueDate"),
            "reference": invoice.get("Reference"),
            "currency_code": invoice.get("CurrencyCode"),
            "currency_rate": invoice.get("CurrencyRate"),
            "line_amount_types": invoice.get("LineAmountTypes"),
            "sub_total": invoice.get("SubTotal"),
            "total_tax": invoice.get("TotalTax"),
            "total": invoice.get("Total"),
            "amount_due": invoice.get("AmountDue"),
            "amount_paid": invoice.get("AmountPaid"),
            "amount_credited": invoice.get("AmountCredited"),
            "fully_paid_on_date": invoice.get("FullyPaidOnDate"),
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
                    "item_code": li.get("ItemCode"),
                    "discount_rate": li.get("DiscountRate"),
                }
                for li in line_items
            ],
            "has_attachments": invoice.get("HasAttachments", False),
            "online_invoice_url": invoice.get("OnlineInvoiceUrl"),
            "updated_date": invoice.get("UpdatedDateUTC"),
        }

    def _format_line_items_for_api(self, line_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format line items for Xero API request."""
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
            if li.get("item_code"):
                xero_li["ItemCode"] = li["item_code"]
            if li.get("discount_rate") is not None:
                xero_li["DiscountRate"] = li["discount_rate"]

            formatted.append(xero_li)
        return formatted
