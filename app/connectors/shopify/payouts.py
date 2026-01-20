"""
Shopify connector - Payout operations
"""

from typing import Any
from urllib.parse import urlencode

from app.http_client import http_client


class ShopifyPayoutsMixin:
    """Shopify payouts operations mixin"""

    def list_payouts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List Shopify Payments payouts"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)

        params = {}
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("date_min"):
            params["date_min"] = args["date_min"]
        if args.get("date_max"):
            params["date_max"] = args["date_max"]

        url = f"{base_url}/shopify_payments/payouts.json"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        payouts = result.get("payouts", [])
        return {
            "payouts": [
                {
                    "id": str(p["id"]),
                    "date": p.get("date"),
                    "amount": p.get("amount"),
                    "status": p.get("status"),
                }
                for p in payouts
            ],
            "count": len(payouts),
        }

    def get_payout(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get payout details"""
        cred = self._get_access_token(org_id, user_id)
        shop_domain = cred.get("shop_domain") or args.get("shop_domain")
        base_url = self._get_base_url(shop_domain)
        payout_id = args["payout_id"]

        result = http_client.get(
            url=f"{base_url}/shopify_payments/payouts/{payout_id}.json",
            service="shopify",
            headers=self._get_headers(cred["access_token"]),
        )

        p = result.get("payout", result)
        return {
            "id": str(p["id"]),
            "date": p.get("date"),
            "amount": p.get("amount"),
            "status": p.get("status"),
        }
