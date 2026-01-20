"""
Xero Bills connector - Accounts Payable (supplier bills) management.

Reference: https://developer.xero.com/documentation/api/accounting/invoices

Bills in Xero are Invoices with Type="ACCPAY".
This module handles ACCPAY invoices (bills from suppliers).
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .invoices import InvoicesMixin

logger = get_logger(__name__)


class BillsMixin(InvoicesMixin):
    """Mixin providing bills (AP) management capabilities."""

    def list_bills(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List bills (supplier invoices) with optional filtering.

        Args:
            where: Filter expression
            order: Sort field (e.g., "Date DESC")
            page: Page number (1-indexed)
            status: Filter by status - "DRAFT", "SUBMITTED", "AUTHORISED", "PAID", "VOIDED"
            contact_id: Filter by supplier
            date_from: Filter bills from this date (YYYY-MM-DD)
            date_to: Filter bills to this date (YYYY-MM-DD)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}
        where_clauses: list[str] = ['Type=="ACCPAY"']  # Only bills

        if args.get("where"):
            where_clauses.append(args["where"])

        if args.get("status"):
            where_clauses.append(f'Status=="{args["status"]}"')

        if args.get("contact_id"):
            where_clauses.append(f'Contact.ContactID==GUID("{args["contact_id"]}")')

        if args.get("date_from"):
            where_clauses.append(f'Date>=DateTime({args["date_from"].replace("-", ",")})')

        if args.get("date_to"):
            where_clauses.append(f'Date<=DateTime({args["date_to"].replace("-", ",")})')

        params["where"] = " AND ".join(where_clauses)

        if args.get("order"):
            params["order"] = args["order"]
        else:
            params["order"] = "Date DESC"

        page = args.get("page", 1)
        params["page"] = page

        result = self._make_api_call("GET", "Invoices", cred, tenant_id, params=params)
        bills = result.get("Invoices", [])

        logger.info(
            "Xero bills listed",
            service="xero",
            count=len(bills),
            page=page,
            log_event="bills_listed",
        )

        return {
            "bills": [self._format_bill(bill) for bill in bills],
            "count": len(bills),
            "page": page,
            "status": "success",
        }

    def get_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific bill by ID.

        Args:
            bill_id: Xero InvoiceID (UUID) for the bill
            invoice_number: Alternative - invoice number from supplier
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        bill_id = args.get("bill_id") or args.get("invoice_number")
        if not bill_id:
            raise ValidationError("bill_id", "bill_id or invoice_number required")

        result = self._make_api_call("GET", f"Invoices/{bill_id}", cred, tenant_id)
        bills = result.get("Invoices", [])

        if not bills:
            return {"bill": None, "status": "not_found"}

        bill = bills[0]
        # Verify it's actually a bill
        if bill.get("Type") != "ACCPAY":
            return {"bill": None, "status": "not_found", "error": "Invoice is not a bill (ACCPAY)"}

        logger.info(
            "Xero bill retrieved",
            service="xero",
            bill_id=bill.get("InvoiceID"),
            log_event="bill_retrieved",
        )

        return {"bill": self._format_bill(bill), "status": "success"}

    def create_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new bill (supplier invoice).

        Args:
            contact_id: Supplier ContactID (required)
            line_items: List of line items (required)
                - description: Item description
                - quantity: Quantity (default 1)
                - unit_amount: Unit price
                - account_code: Expense account code
                - tax_type: Tax type code
                - tracking: Optional tracking categories
            date: Bill date (YYYY-MM-DD, default today)
            due_date: Due date (YYYY-MM-DD)
            invoice_number: Supplier's invoice number
            reference: Reference/PO number
            currency_code: Currency code
            status: DRAFT, SUBMITTED, or AUTHORISED
            line_amount_types: "Exclusive", "Inclusive", or "NoTax"
            url: URL for the bill document
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("contact_id"):
            raise ValidationError("contact_id", "Supplier contact_id is required")
        if not args.get("line_items"):
            raise ValidationError("line_items", "At least one line item is required")

        bill_data: dict[str, Any] = {
            "Type": "ACCPAY",  # Bill (accounts payable)
            "Contact": {"ContactID": args["contact_id"]},
            "LineItems": self._format_bill_line_items_for_api(args["line_items"]),
        }

        # Optional fields
        if args.get("date"):
            bill_data["Date"] = args["date"]
        if args.get("due_date"):
            bill_data["DueDate"] = args["due_date"]
        if args.get("invoice_number"):
            bill_data["InvoiceNumber"] = args["invoice_number"]
        if args.get("reference"):
            bill_data["Reference"] = args["reference"]
        if args.get("currency_code"):
            bill_data["CurrencyCode"] = args["currency_code"]
        if args.get("status"):
            bill_data["Status"] = args["status"]
        else:
            bill_data["Status"] = "DRAFT"
        if args.get("line_amount_types"):
            bill_data["LineAmountTypes"] = args["line_amount_types"]
        if args.get("url"):
            bill_data["Url"] = args["url"]

        result = self._make_api_call(
            "POST", "Invoices", cred, tenant_id, data={"Invoices": [bill_data]}
        )

        created = result.get("Invoices", [])[0] if result.get("Invoices") else {}

        logger.info(
            "Xero bill created",
            service="xero",
            bill_id=created.get("InvoiceID"),
            invoice_number=created.get("InvoiceNumber"),
            total=created.get("Total"),
            log_event="bill_created",
        )

        return {"bill": self._format_bill(created), "status": "success"}

    def update_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an existing bill (DRAFT or SUBMITTED only).

        Args:
            bill_id: Xero InvoiceID (required)
            ... (same optional fields as create_bill)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        bill_id = args.get("bill_id")
        if not bill_id:
            raise ValidationError("bill_id", "bill_id is required")

        bill_data: dict[str, Any] = {"InvoiceID": bill_id}

        if args.get("contact_id"):
            bill_data["Contact"] = {"ContactID": args["contact_id"]}
        if args.get("line_items"):
            bill_data["LineItems"] = self._format_bill_line_items_for_api(args["line_items"])
        if args.get("date"):
            bill_data["Date"] = args["date"]
        if args.get("due_date"):
            bill_data["DueDate"] = args["due_date"]
        if args.get("invoice_number"):
            bill_data["InvoiceNumber"] = args["invoice_number"]
        if args.get("reference"):
            bill_data["Reference"] = args["reference"]
        if args.get("status"):
            bill_data["Status"] = args["status"]

        result = self._make_api_call(
            "POST", f"Invoices/{bill_id}", cred, tenant_id, data={"Invoices": [bill_data]}
        )

        updated = result.get("Invoices", [])[0] if result.get("Invoices") else {}
        logger.info(
            "Xero bill updated",
            service="xero",
            bill_id=bill_id,
            log_event="bill_updated",
        )

        return {"bill": self._format_bill(updated), "status": "success"}

    def void_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Void a bill.

        Args:
            bill_id: Xero InvoiceID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        bill_id = args.get("bill_id")
        if not bill_id:
            raise ValidationError("bill_id", "bill_id is required")

        bill_data = {"InvoiceID": bill_id, "Status": "VOIDED"}

        self._make_api_call(
            "POST", f"Invoices/{bill_id}", cred, tenant_id, data={"Invoices": [bill_data]}
        )

        logger.info(
            "Xero bill voided",
            service="xero",
            bill_id=bill_id,
            log_event="bill_voided",
        )

        return {"bill_id": bill_id, "status": "voided"}

    def get_outstanding_bills(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get all outstanding (unpaid) bills.

        Args:
            contact_id: Optional - filter by supplier
            overdue_only: If true, only return overdue bills
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        where_clauses: list[str] = [
            'Type=="ACCPAY"',
            'Status=="AUTHORISED"',
            "AmountDue>0",
        ]

        if args.get("contact_id"):
            where_clauses.append(f'Contact.ContactID==GUID("{args["contact_id"]}")')

        if args.get("overdue_only"):
            from datetime import datetime

            today = datetime.utcnow().strftime("%Y,%m,%d")
            where_clauses.append(f"DueDate<DateTime({today})")

        params = {"where": " AND ".join(where_clauses), "order": "DueDate ASC"}

        result = self._make_api_call("GET", "Invoices", cred, tenant_id, params=params)
        bills = result.get("Invoices", [])

        total_outstanding = sum(bill.get("AmountDue", 0) for bill in bills)

        logger.info(
            "Xero outstanding bills retrieved",
            service="xero",
            count=len(bills),
            total_outstanding=total_outstanding,
            log_event="outstanding_bills_retrieved",
        )

        return {
            "bills": [self._format_bill(bill) for bill in bills],
            "count": len(bills),
            "total_outstanding": total_outstanding,
            "status": "success",
        }

    def get_ap_aging(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get accounts payable aging summary.

        This calculates aging buckets from outstanding bills.
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params = {
            "where": 'Type=="ACCPAY" AND Status=="AUTHORISED" AND AmountDue>0',
            "order": "DueDate ASC",
        }

        result = self._make_api_call("GET", "Invoices", cred, tenant_id, params=params)
        bills = result.get("Invoices", [])

        from datetime import datetime

        today = datetime.utcnow()
        aging: dict[str, dict[str, float]] = {
            "current": {"amount": 0.0, "count": 0},
            "1_30_days": {"amount": 0.0, "count": 0},
            "31_60_days": {"amount": 0.0, "count": 0},
            "61_90_days": {"amount": 0.0, "count": 0},
            "over_90_days": {"amount": 0.0, "count": 0},
        }

        for bill in bills:
            amount_due = bill.get("AmountDue", 0)
            due_date_str = bill.get("DueDate", "")
            if not due_date_str:
                continue

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
            "Xero AP aging calculated",
            service="xero",
            total_outstanding=total,
            log_event="ap_aging_calculated",
        )

        return {
            "aging": aging,
            "total_outstanding": total,
            "bill_count": len(bills),
            "status": "success",
        }

    def _format_bill(self, bill: dict[str, Any]) -> dict[str, Any]:
        """Format a Xero bill for API response."""
        contact = bill.get("Contact", {})
        line_items = bill.get("LineItems", [])

        return {
            "bill_id": bill.get("InvoiceID"),
            "invoice_number": bill.get("InvoiceNumber"),
            "type": bill.get("Type"),
            "status": bill.get("Status"),
            "supplier": {
                "contact_id": contact.get("ContactID"),
                "name": contact.get("Name"),
            },
            "date": bill.get("Date"),
            "due_date": bill.get("DueDate"),
            "reference": bill.get("Reference"),
            "currency_code": bill.get("CurrencyCode"),
            "currency_rate": bill.get("CurrencyRate"),
            "line_amount_types": bill.get("LineAmountTypes"),
            "sub_total": bill.get("SubTotal"),
            "total_tax": bill.get("TotalTax"),
            "total": bill.get("Total"),
            "amount_due": bill.get("AmountDue"),
            "amount_paid": bill.get("AmountPaid"),
            "amount_credited": bill.get("AmountCredited"),
            "fully_paid_on_date": bill.get("FullyPaidOnDate"),
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
                    "tracking": li.get("Tracking", []),
                }
                for li in line_items
            ],
            "has_attachments": bill.get("HasAttachments", False),
            "updated_date": bill.get("UpdatedDateUTC"),
        }

    def _format_bill_line_items_for_api(
        self, line_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format bill line items for Xero API request."""
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

            # Tracking categories for cost centers/departments
            if li.get("tracking"):
                xero_li["Tracking"] = [
                    {"Name": t.get("name"), "Option": t.get("option")} for t in li["tracking"]
                ]

            formatted.append(xero_li)
        return formatted
