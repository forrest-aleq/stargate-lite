"""
FCI Cash Mixin.

Aggregates cash position across all connected bank accounts:
- Plaid-linked accounts
- Mercury
- Brex
- Chase
- Ramp
- Stripe
- Sage Intacct bank accounts

Returns total cash with account breakdown, change tracking, and trend data.
"""

from datetime import UTC, datetime
from typing import Any

from app.logging_config import get_logger
from app.utilities.fci.service_mappings import CASH_SERVICES

logger = get_logger(__name__)


class CashMixin:
    """Mixin for cash position aggregation."""

    def get_cash(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get total cash position across all connected bank accounts.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - include_pending: Include pending transactions (default: False)
                - currency: Currency for aggregation (default: USD)
                - period: Comparison period (mtd, last_month, etc.)

        Returns:
            {
                "total": float,
                "currency": str,
                "accounts": [{name, bank, balance, type, account_id}],
                "change": float,
                "changePercent": float,
                "trend": [{date, value}],
                "insight": str,
                "lastUpdated": str,
                "sources": [str],
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        include_pending = args.get("include_pending", False)
        currency = args.get("currency", "USD")
        period = args.get("period", "mtd")

        # Aggregate from all cash services
        results, errors, sources = self._aggregate_from_services(
            CASH_SERVICES, org_id, user_id, args
        )

        # Parse results from each service into unified account format
        accounts: list[dict[str, Any]] = []

        for result in results:
            source = result.get("_source", "unknown")
            parsed = self._parse_cash_result(source, result, include_pending)
            accounts.extend(parsed)

        # Calculate total
        total = sum(a.get("balance", 0) for a in accounts)

        # Historical snapshots are not available here; only return snapshot-derived deltas.
        prior_total = self._get_prior_cash_balance(org_id, user_id, accounts, period)
        change, change_percent = self._calculate_change(total, prior_total)

        # Trend is snapshot-only until historical series is wired.
        trend = self._generate_cash_trend(total, change_percent)

        # Keep insight explicit about data quality.
        insight = f"Cash snapshot at ${total:,.0f} across {len(accounts)} account(s)"

        return self._format_response(
            total=total,
            change=change,
            change_percent=change_percent,
            trend=trend,
            insight=insight,
            sources=sources,
            errors=errors if errors else None,
            currency=currency,
            accounts=accounts,
            account_count=len(accounts),
            data_quality={
                "historical_comparison": "unavailable",
                "trend_mode": "snapshot_only",
            },
        )

    def _parse_cash_result(
        self,
        service: str,
        result: dict[str, Any],
        include_pending: bool,
    ) -> list[dict[str, Any]]:
        """
        Parse cash result from a specific service into unified account format.
        Each service returns data differently, so we normalize here.
        """
        accounts: list[dict[str, Any]] = []

        if service == "plaid":
            # Plaid returns accounts with balances
            # current = total balance (includes pending)
            # available = withdrawable funds (excludes pending)
            for account in result.get("accounts", []):
                balance = account.get("balances", {})
                current = balance.get("current", 0) or 0

                if not include_pending:
                    # Use available balance (excludes pending) if requested
                    available = balance.get("available")
                    if available is not None:
                        current = available

                accounts.append(
                    {
                        "name": account.get("name", "Unknown Account"),
                        "bank": account.get("institution_name", "Plaid-linked Bank"),
                        "balance": current,
                        "type": account.get("subtype", account.get("type", "checking")),
                        "account_id": f"plaid:{account.get('account_id', '')}",
                        "currency": balance.get("iso_currency_code", "USD"),
                    }
                )

        elif service == "mercury":
            # Mercury returns list of accounts
            accounts.extend(
                {
                    "name": account.get("name", "Mercury Account"),
                    "bank": "Mercury",
                    "balance": account.get("current_balance", 0),
                    "type": account.get("type", "checking"),
                    "account_id": f"mercury:{account.get('id', '')}",
                    "currency": "USD",
                }
                for account in result.get("accounts", [])
            )

        elif service == "brex":
            # Brex returns cash account info
            balance = result.get("available_balance", {})
            accounts.append(
                {
                    "name": "Brex Cash Account",
                    "bank": "Brex",
                    "balance": balance.get("amount", 0) / 100,  # Brex uses cents
                    "type": "cash",
                    "account_id": f"brex:{result.get('id', 'cash')}",
                    "currency": balance.get("currency", "USD"),
                }
            )

        elif service == "chase":
            # Chase returns account balance
            accounts.append(
                {
                    "name": result.get("account_name", "Chase Business Account"),
                    "bank": "Chase",
                    "balance": result.get("available_balance", result.get("current_balance", 0)),
                    "type": result.get("account_type", "checking"),
                    "account_id": f"chase:{result.get('account_id', '')}",
                    "currency": "USD",
                }
            )

        elif service == "ramp":
            # Ramp - extract balance from transaction response or balance field
            if "balance" in result:
                accounts.append(
                    {
                        "name": "Ramp Account",
                        "bank": "Ramp",
                        "balance": result.get("balance", 0),
                        "type": "credit",
                        "account_id": "ramp:main",
                        "currency": "USD",
                    }
                )

        elif service == "stripe":
            # Stripe returns balance object
            available = result.get("available", [])
            pending = result.get("pending", [])

            for bal in available:
                amount = bal.get("amount", 0) / 100  # Stripe uses cents
                if include_pending:
                    # Add pending to available
                    pending_amount = next(
                        (
                            p.get("amount", 0)
                            for p in pending
                            if p.get("currency") == bal.get("currency")
                        ),
                        0,
                    )
                    amount += pending_amount / 100

                accounts.append(
                    {
                        "name": f"Stripe Balance ({bal.get('currency', 'USD').upper()})",
                        "bank": "Stripe",
                        "balance": amount,
                        "type": "payments",
                        "account_id": f"stripe:{bal.get('currency', 'usd')}",
                        "currency": bal.get("currency", "USD").upper(),
                    }
                )

        elif service == "sage_intacct":
            # Sage Intacct checking accounts
            sage_accounts = result.get("checking_accounts", result.get("accounts", []))
            accounts.extend(
                {
                    "name": account.get("NAME", account.get("name", "Sage Account")),
                    "bank": account.get("BANKNAME", "Bank"),
                    "balance": float(account.get("CURRENTBALANCE", account.get("balance", 0))),
                    "type": "checking",
                    "account_id": (
                        f"sage_intacct:{account.get('RECORDNO', account.get('id', ''))}"
                    ),
                    "currency": account.get("CURRENCY", "USD"),
                }
                for account in sage_accounts
            )

        return accounts

    def _get_prior_cash_balance(
        self,
        org_id: str,
        user_id: str,
        current_accounts: list[dict[str, Any]],
        period: str,
    ) -> float:
        """Get prior period cash balance for comparison.

        Until historical snapshots are available, return current total so
        change metrics stay truthful (0 delta vs fabricated estimates).
        """
        current_total = sum(a.get("balance", 0) for a in current_accounts)
        return current_total

    def _generate_cash_trend(
        self,
        current_total: float,
        change_percent: float,
    ) -> list[dict[str, Any]]:
        """Generate trend data points for sparkline visualization."""
        _ = change_percent  # reserved for future historical mode
        today = datetime.now(UTC)
        return [{"date": today.strftime("%Y-%m"), "value": round(current_total, 2)}]
