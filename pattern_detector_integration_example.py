"""
Example: How PatternDetector should call Stargate-lite
Updated to use capability-based API instead of REST endpoints
"""

from datetime import datetime, timedelta
from typing import Any

import requests


class PatternDetectorStargateClient:
    """
    Helper class for PatternDetector to call Stargate-lite
    """

    def __init__(self, stargate_base_url: str, api_key: str):
        self.stargate_base_url = stargate_base_url
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}

    def _execute_capability(
        self, capability_key: str, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a capability and return result"""
        response = requests.post(
            f"{self.stargate_base_url}/api/v1/execute",
            json={
                "capability_key": capability_key,
                "org_id": org_id,
                "user_id": user_id,
                "args": args,
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def fetch_expenses(
        self,
        org_id: str,
        user_id: str,
        entity_id: str = None,
        vendor_id: str = None,
        category: str = None,
        days: int = 180,
    ) -> list[dict[str, Any]]:
        """
        Fetch expenses from QuickBooks via Stargate-lite

        Replaces: GET /expenses?entity_id=X&days=180
        Uses: POST /api/v1/execute with capability_key="qb.query"
        """
        # Build date filter
        start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Build query (QuickBooks uses "Purchase" for expenses)
        query = f"SELECT * FROM Purchase WHERE TxnDate >= '{start_date}'"

        # Add filters
        if vendor_id:
            query += f" AND EntityRef = '{vendor_id}'"
        if category:
            query += f" AND AccountRef = '{category}'"

        # Execute via capability API
        result = self._execute_capability(
            capability_key="qb.query", org_id=org_id, user_id=user_id, args={"query": query}
        )

        # Extract expenses from result
        if result.get("status") == "success":
            expenses = result.get("outputs", {}).get("results", {}).get("Purchase", [])
            return expenses
        else:
            raise Exception(f"Stargate error: {result}")

    def fetch_vendors(self, org_id: str, user_id: str) -> list[dict[str, Any]]:
        """
        Fetch all vendors from QuickBooks via Stargate-lite

        Replaces: GET /vendors?org_id=X
        Uses: POST /api/v1/execute with capability_key="vendor.list"
        """
        result = self._execute_capability(
            capability_key="vendor.list", org_id=org_id, user_id=user_id, args={}
        )

        if result.get("status") == "success":
            vendors = result.get("outputs", {}).get("vendors", [])
            return vendors
        else:
            raise Exception(f"Stargate error: {result}")

    def fetch_vendor_details(self, org_id: str, user_id: str, vendor_id: str) -> dict[str, Any]:
        """Get single vendor by ID"""
        result = self._execute_capability(
            capability_key="vendor.get",
            org_id=org_id,
            user_id=user_id,
            args={"vendor_id": vendor_id},
        )

        if result.get("status") == "success":
            vendor = result.get("outputs", {}).get("vendor", {})
            return vendor
        else:
            raise Exception(f"Stargate error: {result}")


# Example usage in PatternDetector
if __name__ == "__main__":
    client = PatternDetectorStargateClient(
        stargate_base_url="http://localhost:8000",
        api_key="your-super-secret-internal-api-key-change-this",
    )

    # Fetch expenses from last 180 days
    expenses = client.fetch_expenses(org_id="test_org", user_id="te", days=180)

    print(f"Found {len(expenses)} expenses")

    # Fetch all vendors
    vendors = client.fetch_vendors(org_id="test_org", user_id="te")

    print(f"Found {len(vendors)} vendors")
