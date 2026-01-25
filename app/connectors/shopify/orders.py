"""
Shopify connector - Order operations
"""

from typing import Any
from urllib.parse import urlencode

from app.http_client import http_client


class ShopifyOrdersMixin:
    """Shopify order operations mixin"""

    def list_orders(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List orders from Shopify"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)

        params = {}
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("financial_status"):
            params["financial_status"] = args["financial_status"]
        if args.get("fulfillment_status"):
            params["fulfillment_status"] = args["fulfillment_status"]
        if args.get("created_at_min"):
            params["created_at_min"] = args["created_at_min"]
        if args.get("created_at_max"):
            params["created_at_max"] = args["created_at_max"]
        if args.get("limit"):
            params["limit"] = min(args["limit"], 250)

        url = f"{base_url}/orders.json"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        orders = result.get("orders", [])
        return {
            "orders": [
                {
                    "id": str(o["id"]),
                    "name": o.get("name"),
                    "total_price": o.get("total_price"),
                    "financial_status": o.get("financial_status"),
                    "line_items": o.get("line_items", []),
                }
                for o in orders
            ],
            "count": len(orders),
        }

    def get_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get order details"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)
        order_id = args["order_id"]

        result = http_client.get(
            url=f"{base_url}/orders/{order_id}.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        o = result.get("order", result)
        return {
            "id": str(o["id"]),
            "name": o.get("name"),
            "email": o.get("email"),
            "created_at": o.get("created_at"),
            "total_price": o.get("total_price"),
            "subtotal_price": o.get("subtotal_price"),
            "total_tax": o.get("total_tax"),
            "total_discounts": o.get("total_discounts"),
            "financial_status": o.get("financial_status"),
            "fulfillment_status": o.get("fulfillment_status"),
            "line_items": o.get("line_items", []),
            "shipping_lines": o.get("shipping_lines", []),
            "refunds": o.get("refunds", []),
        }

    def create_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an order in Shopify"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)

        order_data = {
            "line_items": args["line_items"],
        }
        if args.get("customer"):
            order_data["customer"] = args["customer"]
        if args.get("billing_address"):
            order_data["billing_address"] = args["billing_address"]
        if args.get("shipping_address"):
            order_data["shipping_address"] = args["shipping_address"]
        if args.get("financial_status"):
            order_data["financial_status"] = args["financial_status"]
        if args.get("send_receipt"):
            order_data["send_receipt"] = args["send_receipt"]

        result = http_client.post(
            url=f"{base_url}/orders.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
            json={"order": order_data},
        )

        o = result.get("order", result)
        return {
            "id": str(o["id"]),
            "name": o.get("name"),
            "total_price": o.get("total_price"),
        }

    def update_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an order in Shopify"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)
        order_id = args["order_id"]

        order_data = {}
        if args.get("note"):
            order_data["note"] = args["note"]
        if args.get("tags"):
            order_data["tags"] = args["tags"]
        if args.get("email"):
            order_data["email"] = args["email"]
        if args.get("shipping_address"):
            order_data["shipping_address"] = args["shipping_address"]

        result = http_client.put(
            url=f"{base_url}/orders/{order_id}.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
            json={"order": order_data},
        )

        o = result.get("order", result)
        return {
            "id": str(o["id"]),
            "updated_at": o.get("updated_at"),
        }

    def cancel_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Cancel an order in Shopify"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)
        order_id = args["order_id"]

        cancel_data = {}
        if args.get("reason"):
            cancel_data["reason"] = args["reason"]
        if args.get("restock") is not None:
            cancel_data["restock"] = args["restock"]
        if args.get("email") is not None:
            cancel_data["email"] = args["email"]

        result = http_client.post(
            url=f"{base_url}/orders/{order_id}/cancel.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
            json=cancel_data,
        )

        o = result.get("order", result)
        return {
            "id": str(o["id"]),
            "cancelled_at": o.get("cancelled_at"),
        }

    def list_transactions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List transactions for an order"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)
        order_id = args["order_id"]

        result = http_client.get(
            url=f"{base_url}/orders/{order_id}/transactions.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        transactions = result.get("transactions", [])
        return {
            "transactions": [
                {
                    "id": str(t["id"]),
                    "kind": t.get("kind"),
                    "gateway": t.get("gateway"),
                    "amount": t.get("amount"),
                    "status": t.get("status"),
                }
                for t in transactions
            ],
            "count": len(transactions),
        }

    def create_refund(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a refund for an order"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)
        order_id = args["order_id"]

        refund_data = {}
        if args.get("notify") is not None:
            refund_data["notify"] = args["notify"]
        if args.get("note"):
            refund_data["note"] = args["note"]
        if args.get("shipping"):
            refund_data["shipping"] = args["shipping"]
        if args.get("refund_line_items"):
            refund_data["refund_line_items"] = args["refund_line_items"]
        if args.get("transactions"):
            refund_data["transactions"] = args["transactions"]

        result = http_client.post(
            url=f"{base_url}/orders/{order_id}/refunds.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
            json={"refund": refund_data},
        )

        r = result.get("refund", result)
        total_refunded = sum(float(t.get("amount", 0)) for t in r.get("transactions", []))
        return {
            "refund_id": str(r["id"]),
            "total_refunded": str(total_refunded),
            "status": "created",
        }
