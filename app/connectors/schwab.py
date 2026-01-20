"""
Charles Schwab connector for Stargate Lite
Handles trading, accounts, market data, orders
Uses Schwab Trader API v1 (October 2025)
"""

import os
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class SchwabConnector:
    """Charles Schwab Trader API connector"""

    BASE_URL = "https://api.schwabapi.com/trader/v1"
    MARKET_DATA_URL = "https://api.schwabapi.com/marketdata/v1"

    def __init__(self) -> None:
        self.client_id = os.getenv("SCHWAB_CLIENT_ID")
        self.client_secret = os.getenv("SCHWAB_CLIENT_SECRET")

    def _get_access_token(self, args: dict[str, Any]) -> str:
        """Extract and validate access_token from args."""
        access_token = args.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("access_token is required and must be a string")
        return access_token

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _make_request(
        self,
        method: str,
        base_url: str,
        endpoint: str,
        access_token: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{base_url}{endpoint}"
        headers = self._get_headers(access_token)

        if method not in ["GET", "POST", "PUT", "DELETE"]:
            raise ValueError(f"Unsupported method: {method}")

        # Handle GET with params vs others with JSON
        if method == "GET":
            result: dict[str, Any] = http_client.get(
                url=url, service="schwab", headers=headers, params=data
            )
            return result
        # method in ["DELETE", "POST", "PUT"]
        response = http_client.request(
            method=method, url=url, service="schwab", headers=headers, json=data, parse_json=False
        )
        if response.status_code == 204 or not response.text:
            return {"status": "success"}
        json_result: dict[str, Any] = response.json()
        return json_result

    def get_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get all linked accounts with balances and positions"""
        access_token = self._get_access_token(args)

        params = {
            "fields": args.get("fields", "positions")  # Can include "positions"
        }

        result = self._make_request("GET", self.BASE_URL, "/accounts", access_token, params)

        # API may return list directly or wrapped in a dict
        accounts_list = result.get("accounts", []) if isinstance(result, dict) else []
        return {
            "accounts": [
                {
                    "account_number": acc.get("accountNumber"),
                    "account_hash": acc.get("hashValue"),
                    "account_type": acc.get("type"),
                    "round_trips": acc.get("roundTrips"),
                    "is_day_trader": acc.get("isDayTrader"),
                    "is_closing_only_restricted": acc.get("isClosingOnlyRestricted"),
                }
                for acc in accounts_list
                if isinstance(acc, dict)
            ]
        }

    def get_account(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get account details with positions and balances"""
        access_token = self._get_access_token(args)
        account_hash = args.get("account_hash")  # Must use hashed account number

        params = {"fields": args.get("fields", "positions")}

        result = self._make_request(
            "GET", self.BASE_URL, f"/accounts/{account_hash}", access_token, params
        )

        return {
            "account": {
                "account_number": result.get("securitiesAccount", {}).get("accountNumber"),
                "type": result.get("securitiesAccount", {}).get("type"),
                "current_balances": result.get("securitiesAccount", {}).get("currentBalances"),
                "initial_balances": result.get("securitiesAccount", {}).get("initialBalances"),
                "positions": result.get("securitiesAccount", {}).get("positions", []),
            }
        }

    def get_positions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get positions for an account"""
        access_token = self._get_access_token(args)
        account_hash = args.get("account_hash")

        params = {"fields": "positions"}

        result = self._make_request(
            "GET", self.BASE_URL, f"/accounts/{account_hash}", access_token, params
        )

        positions = result.get("securitiesAccount", {}).get("positions", [])

        return {
            "positions": [
                {
                    "short_quantity": pos.get("shortQuantity"),
                    "average_price": pos.get("averagePrice"),
                    "current_day_cost": pos.get("currentDayCost"),
                    "current_day_profit_loss": pos.get("currentDayProfitLoss"),
                    "long_quantity": pos.get("longQuantity"),
                    "settled_long_quantity": pos.get("settledLongQuantity"),
                    "settled_short_quantity": pos.get("settledShortQuantity"),
                    "instrument": {
                        "symbol": pos.get("instrument", {}).get("symbol"),
                        "cusip": pos.get("instrument", {}).get("cusip"),
                        "asset_type": pos.get("instrument", {}).get("assetType"),
                    },
                    "market_value": pos.get("marketValue"),
                }
                for pos in positions
            ]
        }

    def place_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Place a trading order"""
        access_token = self._get_access_token(args)
        account_hash = args.get("account_hash")

        # Build order specification
        order_spec = {
            # MARKET, LIMIT, STOP, STOP_LIMIT
            "orderType": args.get("order_type", "LIMIT"),
            # NORMAL, AM, PM, SEAMLESS
            "session": args.get("session", "NORMAL"),
            # DAY, GOOD_TILL_CANCEL, FILL_OR_KILL
            "duration": args.get("duration", "DAY"),
            # SINGLE, OCO, TRIGGER
            "orderStrategyType": args.get("strategy_type", "SINGLE"),
            "orderLegCollection": [
                {
                    # BUY, SELL, BUY_TO_COVER, SELL_SHORT
                    "instruction": args.get("instruction"),
                    "quantity": args.get("quantity"),
                    "instrument": {
                        "symbol": args.get("symbol"),
                        # EQUITY, OPTION, MUTUAL_FUND, etc.
                        "assetType": args.get("asset_type", "EQUITY"),
                    },
                }
            ],
        }

        # Add price for limit orders
        if args.get("price"):
            order_spec["price"] = args["price"]

        # Add stop price for stop orders
        if args.get("stop_price"):
            order_spec["stopPrice"] = args["stop_price"]

        self._make_request(
            "POST", self.BASE_URL, f"/accounts/{account_hash}/orders", access_token, order_spec
        )

        # Schwab returns order ID in Location header, but we'll return success status
        return {"status": "order_placed", "order_spec": order_spec}

    def get_orders(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get orders for an account"""
        access_token = self._get_access_token(args)
        account_hash = args.get("account_hash")

        params = {
            "fromEnteredTime": args.get("from_entered_time"),  # ISO-8601 format
            "toEnteredTime": args.get("to_entered_time"),
            # AWAITING_PARENT_ORDER, AWAITING_CONDITION, etc.
            "status": args.get("status"),
        }

        result = self._make_request(
            "GET", self.BASE_URL, f"/accounts/{account_hash}/orders", access_token, params
        )

        orders_list: list[dict[str, Any]] = result if isinstance(result, list) else []
        return {
            "orders": [
                {
                    "order_id": order.get("orderId"),
                    "session": order.get("session"),
                    "duration": order.get("duration"),
                    "order_type": order.get("orderType"),
                    "status": order.get("status"),
                    "entered_time": order.get("enteredTime"),
                    "filled_quantity": order.get("filledQuantity"),
                    "remaining_quantity": order.get("remainingQuantity"),
                    "order_leg_collection": order.get("orderLegCollection", []),
                }
                for order in orders_list
            ]
        }

    def cancel_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Cancel an order"""
        access_token = self._get_access_token(args)
        account_hash = args.get("account_hash")
        order_id = args.get("order_id")

        self._make_request(
            "DELETE", self.BASE_URL, f"/accounts/{account_hash}/orders/{order_id}", access_token
        )

        return {"order_id": order_id, "status": "cancelled"}

    def replace_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Replace/modify an existing order"""
        access_token = self._get_access_token(args)
        account_hash = args.get("account_hash")
        order_id = args.get("order_id")

        # New order specification
        order_spec = {
            "orderType": args.get("order_type", "LIMIT"),
            "session": args.get("session", "NORMAL"),
            "duration": args.get("duration", "DAY"),
            "orderStrategyType": args.get("strategy_type", "SINGLE"),
            "orderLegCollection": [
                {
                    "instruction": args.get("instruction"),
                    "quantity": args.get("quantity"),
                    "instrument": {
                        "symbol": args.get("symbol"),
                        "assetType": args.get("asset_type", "EQUITY"),
                    },
                }
            ],
        }

        if args.get("price"):
            order_spec["price"] = args["price"]

        if args.get("stop_price"):
            order_spec["stopPrice"] = args["stop_price"]

        self._make_request(
            "PUT",
            self.BASE_URL,
            f"/accounts/{account_hash}/orders/{order_id}",
            access_token,
            order_spec,
        )

        return {"order_id": order_id, "status": "replaced"}

    def get_quote(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get quote for a single symbol"""
        access_token = self._get_access_token(args)
        symbol = args.get("symbol")

        params = {
            # quote, fundamental, extended, reference, regular
            "fields": args.get("fields", "quote,fundamental")
        }

        result = self._make_request(
            "GET", self.MARKET_DATA_URL, f"/{symbol}/quotes", access_token, params
        )

        return {"quote": result}

    def get_quotes(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get quotes for multiple symbols"""
        access_token = self._get_access_token(args)
        symbols = args.get("symbols")  # Comma-separated string

        params = {"symbols": symbols, "fields": args.get("fields", "quote,fundamental")}

        result = self._make_request("GET", self.MARKET_DATA_URL, "/quotes", access_token, params)

        return {"quotes": result}

    def get_price_history(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get price history for a symbol"""
        access_token = self._get_access_token(args)

        params = {
            "periodType": args.get("period_type", "day"),  # day, month, year, ytd
            "period": args.get("period", 10),
            "frequencyType": args.get("frequency_type", "minute"),  # minute, daily, weekly, monthly
            "frequency": args.get("frequency", 1),
            "startDate": args.get("start_date"),  # Epoch milliseconds
            "endDate": args.get("end_date"),
            "needExtendedHoursData": args.get("need_extended_hours_data", "false"),
        }

        result = self._make_request(
            "GET", self.MARKET_DATA_URL, "/pricehistory", access_token, params
        )

        return {
            "candles": result.get("candles", []),
            "symbol": result.get("symbol"),
            "empty": result.get("empty", False),
        }

    def get_option_chain(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get option chain for a symbol"""
        access_token = self._get_access_token(args)

        params = {
            "symbol": args.get("symbol"),
            "contractType": args.get("contract_type", "ALL"),  # CALL, PUT, ALL
            "strikeCount": args.get("strike_count", 25),
            "includeQuotes": args.get("include_quotes", "TRUE"),
            "strategy": args.get("strategy", "SINGLE"),  # SINGLE, ANALYTICAL, COVERED, etc.
            "range": args.get("range", "ALL"),  # ITM, NTM, OTM, etc.
            "fromDate": args.get("from_date"),  # yyyy-MM-dd
            "toDate": args.get("to_date"),
        }

        result = self._make_request("GET", self.MARKET_DATA_URL, "/chains", access_token, params)

        return {
            "symbol": result.get("symbol"),
            "status": result.get("status"),
            "call_exp_date_map": result.get("callExpDateMap", {}),
            "put_exp_date_map": result.get("putExpDateMap", {}),
        }

    def get_transactions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get transaction history for an account"""
        access_token = self._get_access_token(args)
        account_hash = args.get("account_hash")

        params = {
            # TRADE, RECEIVE_AND_DELIVER, DIVIDEND, etc.
            "types": args.get("types", "TRADE"),
            "startDate": args.get("start_date"),  # ISO-8601
            "endDate": args.get("end_date"),
            "symbol": args.get("symbol"),
        }

        result = self._make_request(
            "GET", self.BASE_URL, f"/accounts/{account_hash}/transactions", access_token, params
        )

        txn_list: list[dict[str, Any]] = result if isinstance(result, list) else []
        return {
            "transactions": [
                {
                    "transaction_id": txn.get("transactionId"),
                    "activity_id": txn.get("activityId"),
                    "type": txn.get("type"),
                    "status": txn.get("status"),
                    "trade_date": txn.get("tradeDate"),
                    "settlement_date": txn.get("settlementDate"),
                    "net_amount": txn.get("netAmount"),
                    "transaction_item": txn.get("transactionItem"),
                }
                for txn in txn_list
            ]
        }
