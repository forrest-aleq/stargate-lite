"""
Interactive Brokers connector for Stargate Lite
Handles trading, portfolio, market data, orders
Uses IBKR Client Portal API (October 2025)
"""

from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class IBKRConnector:
    """Interactive Brokers Client Portal API connector"""

    # Gateway runs locally on localhost:5000 by default
    BASE_URL = "https://localhost:5000/v1/api"

    def __init__(self) -> None:
        # IBKR uses local Gateway authentication
        # No API keys needed - uses session-based auth after Gateway login
        pass

    def _get_headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json", "Accept": "application/json"}

    def _make_request(self, method: str, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Make request to IBKR API. Returns dict or list depending on endpoint."""
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()

        if method not in ["GET", "POST", "DELETE"]:
            raise ValueError(f"Unsupported method: {method}")

        # IBKR Gateway uses self-signed cert on localhost - http_client handles verify=False
        if method == "GET":
            return http_client.get(
                url=url, service="ibkr", headers=headers, params=data, verify=False
            )
        # POST, DELETE
        return http_client.request(
            method=method, url=url, service="ibkr", headers=headers, json=data, verify=False
        )

    def authenticate_session(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Initialize brokerage session (required for trading and market data)"""
        result = self._make_request("POST", "/iserver/auth/ssodh/init")

        return {
            "authenticated": result.get("authenticated", False),
            "competing": result.get("competing", False),
            "connected": result.get("connected", False),
            "message": result.get("message", ""),
            "mac": result.get("MAC", ""),
        }

    def get_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get list of accounts for trading"""
        result = self._make_request("GET", "/iserver/accounts")

        return {
            "accounts": result.get("accounts", []),
            "selected_account": result.get("selectedAccount"),
        }

    def get_account_summary(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get account summary with balances and margin"""
        account_id = args.get("account_id")

        result = self._make_request("GET", f"/portfolio/{account_id}/summary")

        return {"account_id": account_id, "summary": result}

    def get_positions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get portfolio positions for account"""
        account_id = args.get("account_id")
        page_id = args.get("page_id", 0)  # For pagination

        result = self._make_request("GET", f"/portfolio/{account_id}/positions/{page_id}")

        raw_positions: list[dict[str, Any]] = result if isinstance(result, list) else []
        positions_list: list[dict[str, Any]] = [
            {
                "conid": pos.get("conid"),
                "account_id": pos.get("accountId"),
                "position": pos.get("position"),
                "market_price": pos.get("mktPrice"),
                "market_value": pos.get("mktValue"),
                "currency": pos.get("currency"),
                "avg_cost": pos.get("avgCost"),
                "avg_price": pos.get("avgPrice"),
                "unrealized_pnl": pos.get("unrealizedPnl"),
                "realized_pnl": pos.get("realizedPnl"),
                "ticker": pos.get("ticker"),
            }
            for pos in raw_positions
        ]
        return {"positions": positions_list}

    def get_pnl(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get profit and loss for account"""
        result = self._make_request("GET", "/iserver/account/pnl/partitioned")

        return {
            "upnl": result.get("upnl", {}),  # Unrealized P&L
            "dpl": result.get("dpl", {}),  # Daily P&L
            "nl": result.get("nl", {}),  # Net Liquidation
        }

    def get_market_data(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get market data snapshot for contracts"""
        conids = args.get("conids")  # Comma-separated contract IDs
        fields = args.get("fields", "31,84,85,86,88")  # Default: Last, Bid, Ask, High, Low

        params = {"conids": conids, "fields": fields}

        result = self._make_request("GET", "/iserver/marketdata/snapshot", params)

        return {"snapshots": result if isinstance(result, list) else [result]}

    def place_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Place a trading order"""
        account_id = args.get("account_id")

        order_data = {
            "acctId": account_id,
            "conid": args.get("conid"),  # Contract ID
            "secType": args.get("sec_type", "STK"),  # STK, OPT, FUT, etc.
            "orderType": args.get("order_type", "LMT"),  # MKT, LMT, STP, etc.
            "side": args.get("side"),  # BUY or SELL
            "quantity": args.get("quantity"),
            "price": args.get("price"),  # For limit orders
            "tif": args.get("tif", "DAY"),  # DAY, GTC, IOC, etc.
        }

        # Optional fields
        if args.get("stop_price"):
            order_data["auxPrice"] = args["stop_price"]

        result = self._make_request(
            "POST", f"/iserver/account/{account_id}/orders", {"orders": [order_data]}
        )

        order_id = result[0].get("order_id") if isinstance(result, list) else result.get("order_id")
        status = (
            result[0].get("order_status")
            if isinstance(result, list)
            else result.get("order_status")
        )
        message = result[0].get("message") if isinstance(result, list) else result.get("message")
        return {"order_id": order_id, "status": status, "message": message}

    def modify_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Modify an existing order"""
        account_id = args.get("account_id")
        order_id = args.get("order_id")

        modify_data = {"acctId": account_id, "orderId": order_id}

        # Update fields
        if args.get("quantity"):
            modify_data["quantity"] = args["quantity"]

        if args.get("price"):
            modify_data["price"] = args["price"]

        if args.get("stop_price"):
            modify_data["auxPrice"] = args["stop_price"]

        result = self._make_request(
            "POST", f"/iserver/account/{account_id}/order/{order_id}", modify_data
        )

        return {
            "order_id": result.get("order_id"),
            "status": result.get("order_status"),
            "message": result.get("message"),
        }

    def cancel_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Cancel an order"""
        account_id = args.get("account_id")
        order_id = args.get("order_id")

        result = self._make_request("DELETE", f"/iserver/account/{account_id}/order/{order_id}")

        return {
            "order_id": order_id,
            "status": "cancelled",
            "message": result.get("msg", "Order cancelled successfully"),
        }

    def get_orders(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get live orders"""
        result = self._make_request("GET", "/iserver/account/orders")

        return {
            "orders": [
                {
                    "order_id": order.get("orderId"),
                    "account": order.get("acct"),
                    "conid": order.get("conid"),
                    "symbol": order.get("ticker"),
                    "side": order.get("side"),
                    "order_type": order.get("orderType"),
                    "quantity": order.get("totalSize"),
                    "filled": order.get("filledQuantity"),
                    "remaining": order.get("remainingQuantity"),
                    "price": order.get("price"),
                    "status": order.get("status"),
                    "order_description": order.get("orderDesc"),
                }
                for order in (result.get("orders", []) if isinstance(result, dict) else result)
            ]
        }

    def get_trades(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get trade history"""
        params = {
            "days": args.get("days", "1")  # Number of days
        }

        result = self._make_request("GET", "/iserver/account/trades", params)

        return {"trades": result if isinstance(result, list) else result.get("trades", [])}

    def get_executions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get execution details"""
        params = {"days": args.get("days", "1")}

        result = self._make_request("GET", "/pa/executions", params)

        return {"executions": result.get("executions", [])}

    def search_contract(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search for contracts by symbol"""
        symbol = args.get("symbol")

        params = {
            "symbol": symbol,
            "name": args.get("name", "true"),  # Include name in search
        }

        result = self._make_request("GET", "/iserver/secdef/search", params)

        contracts_list: list[dict[str, Any]] = result if isinstance(result, list) else []
        return {
            "contracts": [
                {
                    "conid": c.get("conid"),
                    "symbol": c.get("symbol"),
                    "description": c.get("description"),
                    "sec_type": (
                        c.get("sections", [{}])[0].get("secType") if c.get("sections") else None
                    ),
                }
                for c in contracts_list
            ]
        }

    def get_contract_details(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get contract details by conid"""
        conid = args.get("conid")

        result = self._make_request("GET", f"/iserver/contract/{conid}/info")

        return {
            "conid": conid,
            "symbol": result.get("symbol"),
            "sec_type": result.get("sec_type"),
            "exchange": result.get("exchange"),
            "currency": result.get("currency"),
            "contract_description": result.get("con_desc"),
        }

    def get_portfolio_allocation(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get portfolio allocation by sector/asset class"""
        account_id = args.get("account_id")

        result = self._make_request("GET", f"/portfolio/{account_id}/allocation")

        return {
            "allocation": {
                "by_asset_class": result.get("assetClass", {}),
                "by_sector": result.get("sector", {}),
                "by_group": result.get("group", {}),
            }
        }
