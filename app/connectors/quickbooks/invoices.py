"""
QuickBooks Online connector - Invoices module
"""

from datetime import datetime
from typing import Any
from urllib.parse import quote

from app.http_client import http_client


class QuickBooksInvoicesMixin:
    """QuickBooks invoice operations mixin"""

    base_url: str

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token - implemented in base class"""
        raise NotImplementedError

    def create_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an invoice in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        customer_id = args.get("customer_id", "").replace("qb:", "")

        invoice_data: dict[str, Any] = {
            "CustomerRef": {"value": customer_id},
            "Line": args.get("line_items", []),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("due_date"):
            invoice_data["DueDate"] = args["due_date"]
        if args.get("customer_memo"):
            invoice_data["CustomerMemo"] = {"value": args["customer_memo"]}

        url = f"{self.base_url}/{realm_id}/invoice"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=invoice_data,
        )

        invoice = result.get("Invoice", {})
        return {
            "invoice_id": f"qb:{invoice.get('Id')}",
            "doc_number": invoice.get("DocNumber"),
            "total_amount": invoice.get("TotalAmt"),
            "balance": invoice.get("Balance"),
            "status": "pending",
        }

    def get_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get invoice details from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        invoice_id = args.get("invoice_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/invoice/{invoice_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        invoice = result.get("Invoice", {})
        return {
            "invoice_id": f"qb:{invoice.get('Id')}",
            "doc_number": invoice.get("DocNumber"),
            "customer_id": f"qb:{invoice.get('CustomerRef', {}).get('value')}",
            "total_amount": invoice.get("TotalAmt"),
            "balance": invoice.get("Balance"),
            "due_date": invoice.get("DueDate"),
            "email_status": invoice.get("EmailStatus"),
        }

    def send_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send invoice via email through QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        invoice_id = args.get("invoice_id", "").replace("qb:", "")
        email = args.get("email")

        url = (
            f"{self.base_url}/{realm_id}/invoice/{invoice_id}/send?sendTo={quote(str(email or ''))}"
        )
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        invoice = result.get("Invoice", {})
        return {
            "invoice_id": f"qb:{invoice.get('Id')}",
            "email_sent": True,
            "sent_to": email,
            "email_status": invoice.get("EmailStatus"),
        }

    def void_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Void an invoice in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        invoice_id = args.get("invoice_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/invoice/{invoice_id}"
        invoice_response = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )
        invoice_full = invoice_response.get("Invoice", {})

        void_data = {
            "Id": invoice_id,
            "SyncToken": invoice_full.get("SyncToken"),
            "PrivateNote": args.get("void_reason", "Voided via API"),
        }

        url = f"{self.base_url}/{realm_id}/invoice?operation=void"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=void_data,
        )

        invoice = result.get("Invoice", {})
        return {
            "invoice_id": f"qb:{invoice.get('Id')}",
            "voided": True,
            "balance": invoice.get("Balance"),
        }

    def list_invoices(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List invoices from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Invoice"
        conditions = []
        if args.get("customer_id"):
            customer_id = args["customer_id"].replace("qb:", "")
            conditions.append(f"CustomerRef = '{customer_id}'")
        if args.get("unpaid_only"):
            conditions.append("Balance > 0")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += f" MAXRESULTS {args.get('limit', 100)}"

        url = f"{self.base_url}/{realm_id}/query?query={quote(query)}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        invoices = result.get("QueryResponse", {}).get("Invoice", [])
        return {
            "invoices": [
                {
                    "invoice_id": f"qb:{inv.get('Id')}",
                    "doc_number": inv.get("DocNumber"),
                    "customer": inv.get("CustomerRef", {}).get("name"),
                    "total_amount": inv.get("TotalAmt"),
                    "balance": inv.get("Balance"),
                    "due_date": inv.get("DueDate"),
                }
                for inv in invoices
            ],
            "count": len(invoices),
        }

    def list_outstanding_invoices(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List outstanding invoices from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Invoice WHERE Balance > 0"
        if args.get("customer_id"):
            customer_id = args["customer_id"].replace("qb:", "")
            query += f" AND CustomerRef = '{customer_id}'"
        query += f" MAXRESULTS {args.get('limit', 100)}"

        url = f"{self.base_url}/{realm_id}/query?query={quote(query)}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        invoices = result.get("QueryResponse", {}).get("Invoice", [])
        total_outstanding = sum(inv.get("Balance", 0) for inv in invoices)

        return {
            "invoices": [
                {
                    "invoice_id": f"qb:{inv.get('Id')}",
                    "doc_number": inv.get("DocNumber"),
                    "customer": inv.get("CustomerRef", {}).get("name"),
                    "total_amount": inv.get("TotalAmt"),
                    "balance": inv.get("Balance"),
                    "due_date": inv.get("DueDate"),
                }
                for inv in invoices
            ],
            "total_outstanding": total_outstanding,
            "count": len(invoices),
        }
