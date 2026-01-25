"""
Accounting operations for NetSuite connector.

GL transactions, chart of accounts, subsidiaries, and reconciliation.
"""

from typing import Any

from app.logging_config import get_logger

from .vendor_bill_ops import VendorBillMixin

logger = get_logger(__name__)


class AccountingMixin(VendorBillMixin):
    """Mixin with accounting and GL operations."""

    def get_gl_transactions(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Get GL transactions for bank reconciliation.

        Args:
            account_ids: List of account internal IDs to query
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            subsidiary_id: Optional subsidiary filter
            limit: Max results (default 1000)
        """
        cred = self._get_credentials(org_id, user_id)

        account_ids = args.get("account_ids", [])
        from_date = args.get("from_date")
        to_date = args.get("to_date")

        if not from_date or not to_date:
            raise ValueError("from_date and to_date are required")

        # Build account filter
        account_filter = "1=1"
        if account_ids:
            account_filter = f"account IN ({','.join(str(a) for a in account_ids)})"

        query = self._build_gl_query(from_date, to_date, account_filter)

        if args.get("subsidiary_id"):
            query = query.replace(
                "ORDER BY",
                f"AND t.subsidiary = {args['subsidiary_id']} ORDER BY",
            )

        limit = min(int(args.get("limit", 1000)), 1000)
        result = self._make_suiteql_request(cred, query, limit=limit)

        transactions = self._format_gl_transactions(result.get("items", []))

        return {
            "transactions": transactions,
            "count": len(transactions),
            "has_more": result.get("hasMore", False),
        }

    def _build_gl_query(self, from_date: str, to_date: str, account_filter: str) -> str:
        """Build SuiteQL query for GL transactions."""
        return f"""
            SELECT
                tl.id,
                t.tranid,
                t.trandate,
                t.type,
                t.memo AS header_memo,
                tl.account,
                a.acctnumber,
                a.accountsearchdisplayname AS account_name,
                tl.debit,
                tl.credit,
                tl.memo AS line_memo,
                t.entity
            FROM transactionline tl
            INNER JOIN transaction t ON tl.transaction = t.id
            INNER JOIN account a ON tl.account = a.id
            WHERE t.trandate >= TO_DATE('{from_date}', 'YYYY-MM-DD')
              AND t.trandate <= TO_DATE('{to_date}', 'YYYY-MM-DD')
              AND {account_filter}
            ORDER BY t.trandate, t.id, tl.id
        """

    def _format_gl_transactions(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format GL transaction results."""
        return [
            {
                "line_id": item.get("id"),
                "tran_id": item.get("tranid"),
                "tran_date": item.get("trandate"),
                "type": item.get("type"),
                "header_memo": item.get("header_memo"),
                "account_id": item.get("account"),
                "account_number": item.get("acctnumber"),
                "account_name": item.get("account_name"),
                "debit": item.get("debit"),
                "credit": item.get("credit"),
                "line_memo": item.get("line_memo"),
                "entity_id": item.get("entity"),
            }
            for item in items
        ]

    def get_subsidiary_list(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get list of subsidiaries."""
        cred = self._get_credentials(org_id, user_id)

        query = "SELECT id, name, country FROM subsidiary WHERE isinactive = 'F'"
        result = self._make_suiteql_request(cred, query)

        return {
            "subsidiaries": [
                {
                    "subsidiary_id": f"ns:{item.get('id')}",
                    "name": item.get("name"),
                    "country": item.get("country"),
                }
                for item in result.get("items", [])
            ],
            "count": result.get("count", 0),
        }

    def get_account_list(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Get chart of accounts.

        Args:
            account_type: Optional filter (e.g., 'Bank', 'Expense', 'Income')
        """
        cred = self._get_credentials(org_id, user_id)

        conditions = ["isinactive = 'F'"]

        if args.get("account_type"):
            conditions.append(f"accttype = '{args['account_type']}'")

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT id, acctnumber, accountsearchdisplayname, accttype, balance
            FROM account
            WHERE {where_clause}
            ORDER BY acctnumber
        """

        result = self._make_suiteql_request(cred, query, limit=1000)

        return {
            "accounts": [
                {
                    "account_id": f"ns:{item.get('id')}",
                    "account_number": item.get("acctnumber"),
                    "name": item.get("accountsearchdisplayname"),
                    "type": item.get("accttype"),
                    "balance": item.get("balance"),
                }
                for item in result.get("items", [])
            ],
            "count": result.get("count", 0),
        }

    def reconcile_bank_statement(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Compare bank statement balance against NetSuite GL balance.

        Returns variance information for reconciliation tracking.
        """
        cred = self._get_credentials(org_id, user_id)

        account_id = args.get("account_id")
        statement_date = args.get("statement_date")
        ending_balance = args.get("ending_balance")

        # Get GL balance for comparison
        gl_query = f"""
            SELECT SUM(debit) - SUM(credit) AS balance
            FROM transactionline tl
            INNER JOIN transaction t ON tl.transaction = t.id
            WHERE tl.account = {str(account_id).replace('ns:', '')}
              AND t.trandate <= TO_DATE('{statement_date}', 'YYYY-MM-DD')
        """

        result = self._make_suiteql_request(cred, gl_query)
        gl_balance = result.get("items", [{}])[0].get("balance", 0) or 0

        variance = float(ending_balance or 0) - float(gl_balance)

        return {
            "account_id": account_id,
            "statement_date": statement_date,
            "statement_balance": ending_balance,
            "gl_balance": gl_balance,
            "variance": variance,
            "status": "balanced" if abs(variance) < 0.01 else "variance_exists",
        }

    def query_records(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a SuiteQL query.

        Args:
            query: SuiteQL query string
            limit: Max results (default 1000, max 1000 per page)
            offset: Pagination offset
        """
        logger.info(
            "Executing SuiteQL query",
            service="netsuite",
            limit=args.get("limit", 1000),
            log_event="netsuite_suiteql_query",
        )
        cred = self._get_credentials(org_id, user_id)

        query = args.get("query")
        if not query:
            raise ValueError("query is required")

        limit = min(int(args.get("limit", 1000)), 1000)
        offset = int(args.get("offset", 0))

        result = self._make_suiteql_request(cred, query, limit=limit, offset=offset)

        logger.info(
            "SuiteQL query completed",
            service="netsuite",
            result_count=result.get("count", 0),
            log_event="netsuite_suiteql_complete",
        )

        return {
            "items": result.get("items", []),
            "count": result.get("count", 0),
            "has_more": result.get("hasMore", False),
        }
