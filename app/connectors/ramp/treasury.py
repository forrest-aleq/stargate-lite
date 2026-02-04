"""
Ramp treasury mixin for bank accounts, entities, and cashbacks.
Endpoints verified against Ramp OpenAPI spec (2026).
"""

from typing import Any

from .accounting import AccountingMixin


class TreasuryMixin(AccountingMixin):
    """Mixin with treasury operations."""

    def get_bank_account(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get bank account by ID."""
        bank_account_id = args.get("bank_account_id")
        result = self._make_request("GET", f"/bank-accounts/{bank_account_id}", org_id, user_id)

        return {
            "id": result["id"],
            "bank_name": result.get("bank_name"),
            "last_four": result.get("last_four"),
            "status": result.get("status"),
        }

    def list_entities(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List business entities."""
        result = self._make_request("GET", "/entities", org_id, user_id)

        return {
            "entities": [
                {
                    "id": e["id"],
                    "name": e.get("name"),
                    "status": e.get("status"),
                }
                for e in result.get("data", [])
            ],
        }

    def get_entity(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single entity by ID."""
        entity_id = args.get("entity_id")
        result = self._make_request("GET", f"/entities/{entity_id}", org_id, user_id)

        return {
            "id": result["id"],
            "name": result.get("name"),
            "status": result.get("status"),
        }

    def list_cashbacks(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List cashback earnings."""
        params: dict[str, Any] = {"page_size": args.get("page_size", 50)}
        result = self._make_request("GET", "/cashbacks", org_id, user_id, params=params)

        return {
            "cashbacks": [
                {
                    "id": c["id"],
                    "amount": c.get("amount"),
                    "period": c.get("period"),
                }
                for c in result.get("data", [])
            ],
            "page": result.get("page"),
        }

    def get_business(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get company/business info."""
        result = self._make_request("GET", "/business", org_id, user_id)

        return {
            "id": result.get("id"),
            "name": result.get("name"),
            "status": result.get("status"),
        }

    def get_business_balance(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get business balance."""
        result = self._make_request("GET", "/business/balance", org_id, user_id)

        return {
            "balance": result.get("balance"),
            "currency": result.get("currency"),
        }
