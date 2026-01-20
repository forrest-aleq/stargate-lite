"""
QuickBooks Online connector - Items and Documents module
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from app.http_client import http_client


class QuickBooksItemsMixin:
    """QuickBooks items, estimates, and other document operations mixin"""

    base_url: str

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token - implemented in base class"""
        raise NotImplementedError

    def create_item(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an item in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        item_data: dict[str, Any] = {
            "Name": args.get("item_name"),
            "Type": args.get("item_type", "Service"),
        }

        if args.get("income_account_id"):
            item_data["IncomeAccountRef"] = {"value": args["income_account_id"].replace("qb:", "")}
        if args.get("expense_account_id"):
            item_data["ExpenseAccountRef"] = {
                "value": args["expense_account_id"].replace("qb:", "")
            }
        if args.get("unit_price"):
            item_data["UnitPrice"] = args["unit_price"]
        if args.get("description"):
            item_data["Description"] = args["description"]

        url = f"{self.base_url}/{realm_id}/item"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=item_data,
        )

        item = result.get("Item", {})
        return {
            "item_id": f"qb:{item.get('Id')}",
            "name": item.get("Name"),
            "type": item.get("Type"),
            "unit_price": item.get("UnitPrice"),
        }

    def get_item(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get item details from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        item_id = args.get("item_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/item/{item_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        item = result.get("Item", {})
        return {
            "item_id": f"qb:{item.get('Id')}",
            "name": item.get("Name"),
            "type": item.get("Type"),
            "unit_price": item.get("UnitPrice"),
            "description": item.get("Description"),
            "active": item.get("Active"),
        }

    def list_items(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List items from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Item"
        conditions = []
        if args.get("item_type"):
            conditions.append(f"Type = '{args['item_type']}'")
        if args.get("active_only"):
            conditions.append("Active = true")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += f" MAXRESULTS {args.get('limit', 100)}"

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        items = result.get("QueryResponse", {}).get("Item", [])
        return {
            "items": [
                {
                    "item_id": f"qb:{item.get('Id')}",
                    "name": item.get("Name"),
                    "type": item.get("Type"),
                    "unit_price": item.get("UnitPrice"),
                }
                for item in items
            ],
            "count": len(items),
        }

    def create_estimate(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an estimate in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        customer_id = args.get("customer_id", "").replace("qb:", "")

        estimate_data: dict[str, Any] = {
            "CustomerRef": {"value": customer_id},
            "Line": args.get("line_items", []),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("expiration_date"):
            estimate_data["ExpirationDate"] = args["expiration_date"]
        if args.get("customer_memo"):
            estimate_data["CustomerMemo"] = {"value": args["customer_memo"]}

        url = f"{self.base_url}/{realm_id}/estimate"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=estimate_data,
        )

        estimate = result.get("Estimate", {})
        return {
            "estimate_id": f"qb:{estimate.get('Id')}",
            "doc_number": estimate.get("DocNumber"),
            "total_amount": estimate.get("TotalAmt"),
            "customer_id": f"qb:{customer_id}",
            "status": estimate.get("TxnStatus"),
        }

    def get_estimate(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get estimate details from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        estimate_id = args.get("estimate_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/estimate/{estimate_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        estimate = result.get("Estimate", {})
        return {
            "estimate_id": f"qb:{estimate.get('Id')}",
            "doc_number": estimate.get("DocNumber"),
            "customer_id": f"qb:{estimate.get('CustomerRef', {}).get('value')}",
            "total_amount": estimate.get("TotalAmt"),
            "expiration_date": estimate.get("ExpirationDate"),
            "status": estimate.get("TxnStatus"),
        }

    def create_sales_receipt(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a sales receipt in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        customer_id = args.get("customer_id", "").replace("qb:", "")

        receipt_data: dict[str, Any] = {
            "CustomerRef": {"value": customer_id},
            "Line": args.get("line_items", []),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("payment_method"):
            receipt_data["PaymentMethodRef"] = {"name": args["payment_method"]}

        url = f"{self.base_url}/{realm_id}/salesreceipt"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=receipt_data,
        )

        receipt = result.get("SalesReceipt", {})
        return {
            "sales_receipt_id": f"qb:{receipt.get('Id')}",
            "doc_number": receipt.get("DocNumber"),
            "total_amount": receipt.get("TotalAmt"),
            "customer_id": f"qb:{customer_id}",
        }

    def create_credit_memo(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a credit memo in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        customer_id = args.get("customer_id", "").replace("qb:", "")

        memo_data: dict[str, Any] = {
            "CustomerRef": {"value": customer_id},
            "Line": args.get("line_items", []),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        url = f"{self.base_url}/{realm_id}/creditmemo"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=memo_data,
        )

        memo = result.get("CreditMemo", {})
        return {
            "credit_memo_id": f"qb:{memo.get('Id')}",
            "doc_number": memo.get("DocNumber"),
            "total_amount": memo.get("TotalAmt"),
            "customer_id": f"qb:{customer_id}",
            "balance": memo.get("Balance"),
        }

    def upload_attachment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Upload an attachment to a QuickBooks entity"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        file_path_arg = args.get("file_path")
        if not isinstance(file_path_arg, str):
            raise ValueError("file_path must be a string")
        file_path = Path(file_path_arg)
        entity_type = args.get("entity_type")
        entity_id = args.get("entity_id", "").replace("qb:", "")

        with file_path.open("rb") as f:
            file_content = f.read()

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        content_type = f"multipart/form-data; boundary={boundary}"

        filename = file_path.name
        body = (
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file_metadata_0"\r\n'
                f"Content-Type: application/json\r\n\r\n"
                f'{{"AttachableRef":[{{"EntityRef":{{"type":"{entity_type}",'
                f'"value":"{entity_id}"}}}}],"FileName":"{filename}"}}\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file_content_0"; '
                f'filename="{filename}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
            + file_content
            + f"\r\n--{boundary}--".encode()
        )

        url = f"{self.base_url}/{realm_id}/upload"
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": content_type,
            },
            data=body,
            timeout=60,
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Upload failed: {response.text}")

        result = response.json()
        attachable = result.get("AttachableResponse", [{}])[0].get("Attachable", {})
        return {
            "attachment_id": f"qb:{attachable.get('Id')}",
            "file_name": attachable.get("FileName"),
            "size": attachable.get("Size"),
            "entity_type": entity_type,
            "entity_id": f"qb:{entity_id}",
        }
