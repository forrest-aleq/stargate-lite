"""
Square connector - Order operations
"""

from typing import Any

from app.http_client import http_client


class SquareOrdersMixin:
    """Square order operations mixin"""

    def search_orders(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search/list orders from Square"""
        cred = self._get_access_token(org_id, user_id)

        search_data = {
            "location_ids": args["location_ids"],
        }
        if args.get("query"):
            search_data["query"] = args["query"]
        if args.get("limit"):
            search_data["limit"] = args["limit"]
        if args.get("cursor"):
            search_data["cursor"] = args["cursor"]

        result = http_client.post(
            url=f"{self.base_url}/orders/search",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            json=search_data,
        )

        orders = result.get("orders", [])
        return {
            "orders": [
                {
                    "id": o["id"],
                    "location_id": o.get("location_id"),
                    "line_items": o.get("line_items", []),
                    "total_money": o.get("total_money"),
                    "state": o.get("state"),
                }
                for o in orders
            ],
            "cursor": result.get("cursor"),
        }

    def get_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get order details"""
        cred = self._get_access_token(org_id, user_id)
        order_id = args["order_id"]

        result = http_client.get(
            url=f"{self.base_url}/orders/{order_id}",
            service="square",
            headers=self._get_headers(cred["access_token"]),
        )

        o = result.get("order", result)
        return {
            "id": o["id"],
            "location_id": o.get("location_id"),
            "line_items": o.get("line_items", []),
            "total_money": o.get("total_money"),
            "total_tax_money": o.get("total_tax_money"),
            "total_discount_money": o.get("total_discount_money"),
            "state": o.get("state"),
            "tenders": o.get("tenders", []),
            "refunds": o.get("refunds", []),
        }

    def create_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an order in Square"""
        cred = self._get_access_token(org_id, user_id)

        order_data = {
            "idempotency_key": args["idempotency_key"],
            "order": {
                "location_id": args["location_id"],
            },
        }
        if args.get("line_items"):
            order_data["order"]["line_items"] = args["line_items"]
        if args.get("reference_id"):
            order_data["order"]["reference_id"] = args["reference_id"]

        result = http_client.post(
            url=f"{self.base_url}/orders",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            json=order_data,
        )

        o = result.get("order", result)
        return {
            "order_id": o["id"],
            "state": o.get("state"),
        }

    def update_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an order in Square"""
        cred = self._get_access_token(org_id, user_id)
        order_id = args["order_id"]

        update_data = {}
        if args.get("fields_to_clear"):
            update_data["fields_to_clear"] = args["fields_to_clear"]
        if args.get("order"):
            update_data["order"] = args["order"]
        if args.get("idempotency_key"):
            update_data["idempotency_key"] = args["idempotency_key"]

        result = http_client.put(
            url=f"{self.base_url}/orders/{order_id}",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            json=update_data,
        )

        o = result.get("order", result)
        return {
            "order_id": o["id"],
            "version": o.get("version"),
        }

    def pay_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Pay for an order"""
        cred = self._get_access_token(org_id, user_id)
        order_id = args["order_id"]

        pay_data = {
            "idempotency_key": args["idempotency_key"],
        }
        if args.get("payment_ids"):
            pay_data["payment_ids"] = args["payment_ids"]

        result = http_client.post(
            url=f"{self.base_url}/orders/{order_id}/pay",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            json=pay_data,
        )

        o = result.get("order", result)
        return {
            "order_id": o["id"],
            "state": o.get("state"),
        }
