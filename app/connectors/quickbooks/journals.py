"""
QuickBooks Online connector - Journal Entries module
"""

from datetime import datetime
from typing import Any

from app.connectors.quickbooks import deep_links
from app.http_client import http_client


class QuickBooksJournalsMixin:
    """QuickBooks journal entry operations mixin"""

    base_url: str

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token - implemented in base class"""
        raise NotImplementedError

    def create_journal_entry(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a journal entry in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        journal_data: dict[str, Any] = {
            "Line": args.get("lines"),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
            "PrivateNote": args.get("memo", ""),
        }

        if args.get("doc_number"):
            journal_data["DocNumber"] = args["doc_number"]

        url = f"{self.base_url}/{realm_id}/journalentry"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=journal_data,
        )

        je = result.get("JournalEntry", {})
        je_id = je.get("Id")
        return {
            "journal_entry_id": f"qb:{je_id}",
            "doc_number": je.get("DocNumber"),
            "txn_date": je.get("TxnDate"),
            "total_amount": je.get("TotalAmt"),
            "memo": je.get("PrivateNote"),
            "deep_link": deep_links.journal_entry_link(je_id),
        }

    def get_journal_entry(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a journal entry from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        je_id = args.get("journal_entry_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/journalentry/{je_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )
        je = result.get("JournalEntry", {})
        return {
            "journal_entry_id": f"qb:{je.get('Id')}",
            "doc_number": je.get("DocNumber"),
            "txn_date": je.get("TxnDate"),
            "total_amount": je.get("TotalAmt"),
            "memo": je.get("PrivateNote"),
            "lines": je.get("Line", []),
            "deep_link": deep_links.journal_entry_link(je.get("Id")),
        }

    def list_journal_entries(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List journal entries from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        # Sanitize limit to integer (QuickBooks Query Language, not SQL database)
        limit = int(args.get("limit", 100))
        query = f"SELECT * FROM JournalEntry MAXRESULTS {limit}"  # nosec B608

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )
        entries = result.get("QueryResponse", {}).get("JournalEntry", [])
        return {
            "journal_entries": [
                {
                    "journal_entry_id": f"qb:{je.get('Id')}",
                    "doc_number": je.get("DocNumber"),
                    "txn_date": je.get("TxnDate"),
                    "total_amount": je.get("TotalAmt"),
                    "deep_link": deep_links.journal_entry_link(je.get("Id")),
                }
                for je in entries
            ],
            "count": len(entries),
        }
