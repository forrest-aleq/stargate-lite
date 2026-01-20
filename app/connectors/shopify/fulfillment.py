"""
Shopify connector - Fulfillment operations
"""

from typing import Any

from app.http_client import http_client


class ShopifyFulfillmentMixin:
    """Shopify fulfillment operations mixin"""

    def list_fulfillments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List fulfillments for an order"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)
        order_id = args["order_id"]

        result = http_client.get(
            url=f"{base_url}/orders/{order_id}/fulfillments.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        fulfillments = result.get("fulfillments", [])
        return {
            "fulfillments": [
                {
                    "id": str(f["id"]),
                    "status": f.get("status"),
                    "tracking_number": f.get("tracking_number"),
                    "tracking_company": f.get("tracking_company"),
                    "created_at": f.get("created_at"),
                }
                for f in fulfillments
            ],
            "count": len(fulfillments),
        }

    def create_fulfillment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a fulfillment for an order"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)

        fulfillment_data = {
            "line_items_by_fulfillment_order": args["line_items_by_fulfillment_order"],
        }
        if args.get("tracking_info"):
            fulfillment_data["tracking_info"] = args["tracking_info"]
        if args.get("notify_customer") is not None:
            fulfillment_data["notify_customer"] = args["notify_customer"]

        result = http_client.post(
            url=f"{base_url}/fulfillments.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
            json={"fulfillment": fulfillment_data},
        )

        f = result.get("fulfillment", result)
        return {
            "id": str(f["id"]),
            "order_id": str(f.get("order_id")),
            "status": f.get("status"),
            "tracking_number": f.get("tracking_number"),
        }
