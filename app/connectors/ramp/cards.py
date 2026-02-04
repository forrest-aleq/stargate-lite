"""
Ramp cards mixin for card operations.
"""

from typing import Any

from .transactions import TransactionsMixin


class CardsMixin(TransactionsMixin):
    """Mixin with card operations."""

    def list_cards(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List all cards."""
        params: dict[str, Any] = {"page_size": args.get("page_size", 50)}
        if args.get("user_id_filter"):
            params["user_id"] = args["user_id_filter"]

        result = self._make_request("GET", "/cards", org_id, user_id, params=params)

        return {
            "cards": [
                {
                    "id": c["id"],
                    "display_name": c.get("display_name"),
                    "last_four": c.get("last_four"),
                    "state": c.get("state"),
                    "is_physical": c.get("is_physical"),
                    "user_id": c.get("cardholder_id"),
                }
                for c in result.get("data", [])
            ],
            "page": result.get("page"),
        }

    def get_card(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get a single card by ID."""
        card_id = args.get("card_id")
        result = self._make_request("GET", f"/cards/{card_id}", org_id, user_id)

        return {
            "id": result["id"],
            "display_name": result.get("display_name"),
            "last_four": result.get("last_four"),
            "state": result.get("state"),
            "is_physical": result.get("is_physical"),
            "spending_restrictions": result.get("spending_restrictions"),
        }

    def create_card(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a virtual or physical card."""
        card_data = {
            "user_id": args.get("ramp_user_id"),
            "display_name": args.get("display_name"),
            "spending_restrictions": args.get("spending_restrictions", {}),
            "is_physical": args.get("is_physical", False),
        }

        result = self._make_request("POST", "/cards", org_id, user_id, data=card_data)

        return {
            "card_id": result["id"],
            "last_four": result.get("last_four"),
            "state": result["state"],
            "is_physical": result.get("is_physical"),
        }
