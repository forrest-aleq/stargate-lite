"""
Square connector - Payout operations
"""

from typing import Any

from app.http_client import http_client


class SquarePayoutsMixin:
    """Square payout operations mixin"""

    def list_payouts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List payouts from Square"""
        cred = self._get_access_token(org_id, user_id)

        params = {}
        if args.get("location_id"):
            params["location_id"] = args["location_id"]
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("begin_time"):
            params["begin_time"] = args["begin_time"]
        if args.get("end_time"):
            params["end_time"] = args["end_time"]
        if args.get("cursor"):
            params["cursor"] = args["cursor"]
        if args.get("limit"):
            params["limit"] = args["limit"]

        result = http_client.get(
            url=f"{self.base_url}/payouts",
            service="square",
            headers=self._get_headers(cred["access_token"]),
            params=params,
        )

        payouts = result.get("payouts", [])
        return {
            "payouts": [
                {
                    "id": p["id"],
                    "status": p.get("status"),
                    "amount": p.get("amount_money"),
                    "arrival_date": p.get("arrival_date"),
                }
                for p in payouts
            ],
            "cursor": result.get("cursor"),
        }
