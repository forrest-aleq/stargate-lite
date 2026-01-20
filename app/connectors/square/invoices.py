"""
Square connector - Invoice operations
"""

from typing import Any

from app.http_client import http_client


class SquareInvoicesMixin:
    """Square invoice operations mixin"""

    def list_invoices(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List invoices from Square"""
        cred = self._get_access_token(org_id, user_id)

        params = {"location_id": args["location_id"]}
        if args.get("cursor"):
            params["cursor"] = args["cursor"]
        if args.get("limit"):
            params["limit"] = args["limit"]

        result = http_client.get(
            url=f"{self.base_url}/invoices",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            params=params,
        )

        invoices = result.get("invoices", [])
        return {
            "invoices": [
                {
                    "id": i["id"],
                    "invoice_number": i.get("invoice_number"),
                    "status": i.get("status"),
                    "payment_requests": i.get("payment_requests", []),
                }
                for i in invoices
            ],
            "cursor": result.get("cursor"),
        }

    def get_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get invoice details"""
        cred = self._get_access_token(org_id, user_id)
        invoice_id = args["invoice_id"]

        result = http_client.get(
            url=f"{self.base_url}/invoices/{invoice_id}",
            service="square",
            headers=self._get_headers(cred["access_token"]),
        )

        i = result.get("invoice", result)
        return {
            "id": i["id"],
            "invoice_number": i.get("invoice_number"),
            "status": i.get("status"),
            "version": i.get("version"),
            "primary_recipient": i.get("primary_recipient"),
            "payment_requests": i.get("payment_requests", []),
        }

    def create_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an invoice in Square"""
        cred = self._get_access_token(org_id, user_id)

        invoice_data = {
            "idempotency_key": args["idempotency_key"],
            "invoice": {
                "location_id": args["location_id"],
                "order_id": args["order_id"],
                "primary_recipient": args["primary_recipient"],
                "payment_requests": args["payment_requests"],
            },
        }
        if args.get("delivery_method"):
            invoice_data["invoice"]["delivery_method"] = args["delivery_method"]

        result = http_client.post(
            url=f"{self.base_url}/invoices",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            json=invoice_data,
        )

        i = result.get("invoice", result)
        return {
            "invoice_id": i["id"],
            "invoice_number": i.get("invoice_number"),
            "status": i.get("status"),
        }

    def publish_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Publish a draft invoice"""
        cred = self._get_access_token(org_id, user_id)
        invoice_id = args["invoice_id"]

        publish_data = {
            "version": args["version"],
        }
        if args.get("idempotency_key"):
            publish_data["idempotency_key"] = args["idempotency_key"]

        result = http_client.post(
            url=f"{self.base_url}/invoices/{invoice_id}/publish",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            json=publish_data,
        )

        i = result.get("invoice", result)
        return {
            "invoice_id": i["id"],
            "status": i.get("status"),
            "public_url": i.get("public_url"),
        }
