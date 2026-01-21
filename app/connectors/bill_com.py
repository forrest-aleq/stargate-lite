"""
Bill.com connector for Stargate Lite
Handles vendor payments and AP automation
Uses Bill.com v3 API (October 2025)
"""

import os
from datetime import datetime, timedelta
from typing import Any

from app.database import CredentialManager
from app.errors import CredentialMissingError
from app.http_client import http_client
from app.logging_config import get_logger
from app.posthog_client import track_token_refreshed

logger = get_logger(__name__)


class BillComConnector:
    """Bill.com API connector for AP automation"""

    BASE_URL = "https://api.bill.com/v3"
    SANDBOX_URL = "https://api-sandbox.bill.com/v3"
    AUTH_URL = "https://login.bill.com/oauth/token"

    def __init__(self) -> None:
        self.client_id = os.getenv("BILLCOM_CLIENT_ID")
        self.client_secret = os.getenv("BILLCOM_CLIENT_SECRET")
        self.environment = os.getenv("BILLCOM_ENVIRONMENT", "sandbox")
        self.base_url = self.SANDBOX_URL if self.environment == "sandbox" else self.BASE_URL

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token, refreshing if necessary"""
        cred = CredentialManager.get_credential(org_id, user_id, "billcom")

        if not cred:
            raise CredentialMissingError("billcom", org_id, user_id)

        # Check if token is expired
        if cred["token_expiry"] and cred["token_expiry"] < datetime.utcnow() + timedelta(minutes=5):
            logger.info(
                "Token expired or expiring soon, refreshing",
                service="billcom",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_needed",
            )
            return self._refresh_token(org_id, user_id, cred["refresh_token"])

        return cred

    def _refresh_token(self, org_id: str, user_id: str, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token"""
        logger.info(
            "Refreshing Bill.com token",
            service="billcom",
            org_id=org_id,
            user_id=user_id,
            log_event="token_refresh_start",
        )

        try:
            token_data = http_client.post(
                url=self.AUTH_URL,
                service="billcom",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
            )

            new_expiry = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

            CredentialManager.store_credential(
                org_id=org_id,
                user_id=user_id,
                service="billcom",
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expiry=new_expiry,
            )

            logger.info(
                "Bill.com token refreshed successfully",
                service="billcom",
                org_id=org_id,
                user_id=user_id,
                expires_in_seconds=token_data["expires_in"],
                log_event="token_refresh_success",
            )

            # Track successful token refresh to PostHog
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="billcom",
                success=True,
            )

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_expiry": new_expiry,
            }
        except Exception as e:
            logger.error(
                "Bill.com token refresh failed",
                service="billcom",
                org_id=org_id,
                user_id=user_id,
                error_type=type(e).__name__,
                log_event="token_refresh_error",
                exc_info=True,
            )
            # Track failed token refresh to PostHog
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="billcom",
                success=False,
            )
            raise

    def create_vendor(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a vendor in Bill.com"""
        cred = self._get_access_token(org_id, user_id)

        vendor_data = {
            "name": args.get("vendor_name"),
            "email": args.get("email"),
            "phone": args.get("phone"),
            "accountNumber": args.get("account_number"),
            "paymentTerms": args.get("payment_terms", "NET_30"),
        }

        if args.get("address"):
            vendor_data["address"] = args["address"]

        url = f"{self.base_url}/vendors"
        result = http_client.post(
            url=url,
            service="billcom",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json=vendor_data,
        )

        return {
            "vendor_id": f"bc:{result['id']}",
            "vendor_name": result["name"],
            "email": result.get("email"),
            "status": result.get("status"),
        }

    def create_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a bill in Bill.com"""
        cred = self._get_access_token(org_id, user_id)

        vendor_id = args.get("vendor_id", "").replace("bc:", "")

        bill_data = {
            "vendorId": vendor_id,
            "invoiceNumber": args.get("invoice_number"),
            "invoiceDate": args.get("invoice_date"),
            "dueDate": args.get("due_date"),
            "amount": args.get("amount"),
            "lineItems": args.get("line_items", []),
        }

        if args.get("description"):
            bill_data["description"] = args["description"]

        url = f"{self.base_url}/bills"
        result = http_client.post(
            url=url,
            service="billcom",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json=bill_data,
        )

        return {
            "bill_id": f"bc:{result['id']}",
            "invoice_number": result["invoiceNumber"],
            "amount": result["amount"],
            "status": result.get("status", "open"),
            "due_date": result["dueDate"],
        }

    def create_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a payment in Bill.com"""
        cred = self._get_access_token(org_id, user_id)

        payment_data = {
            "billIds": [bid.replace("bc:", "") for bid in args.get("bill_ids", [])],
            "paymentMethod": args.get("payment_method", "ACH"),  # ACH, WIRE, CHECK
            "processDate": args.get("process_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("amount"):
            payment_data["amount"] = args["amount"]

        url = f"{self.base_url}/payments"
        result = http_client.post(
            url=url,
            service="billcom",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json=payment_data,
        )

        return {
            "payment_id": f"bc:{result['id']}",
            "amount": result.get("amount"),
            "payment_method": result.get("paymentMethod"),
            "status": result.get("status"),
            "process_date": result.get("processDate"),
        }

    def create_bulk_payment(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create bulk payments in Bill.com"""
        cred = self._get_access_token(org_id, user_id)

        payments_data = {
            "payments": args.get("payments", [])  # Array of payment objects
        }

        url = f"{self.base_url}/payments/bulk"
        result = http_client.post(
            url=url,
            service="billcom",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json=payments_data,
        )

        return {
            "batch_id": result.get("batchId"),
            "total_payments": len(result.get("payments", [])),
            "total_amount": sum(p.get("amount", 0) for p in result.get("payments", [])),
            "status": result.get("status"),
        }

    def list_bills(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List bills from Bill.com"""
        cred = self._get_access_token(org_id, user_id)

        params = {"page": args.get("page", 1), "pageSize": args.get("page_size", 50)}

        if args.get("status"):
            params["status"] = args["status"]  # OPEN, PAID, SCHEDULED
        if args.get("vendor_id"):
            params["vendorId"] = args["vendor_id"].replace("bc:", "")

        query_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.base_url}/bills?{query_str}"

        result = http_client.get(
            url=url, service="billcom", headers={"Authorization": f"Bearer {cred['access_token']}"}
        )

        return {
            "bills": [
                {
                    "bill_id": f"bc:{b['id']}",
                    "invoice_number": b.get("invoiceNumber"),
                    "vendor_name": b.get("vendorName"),
                    "amount": b.get("amount"),
                    "due_date": b.get("dueDate"),
                    "status": b.get("status"),
                }
                for b in result.get("bills", [])
            ],
            "total": result.get("total", 0),
            "page": result.get("page", 1),
        }

    def list_vendors(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List vendors from Bill.com"""
        cred = self._get_access_token(org_id, user_id)

        params = {"page": args.get("page", 1), "pageSize": args.get("page_size", 50)}

        if args.get("active_only"):
            params["status"] = "ACTIVE"

        query_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.base_url}/vendors?{query_str}"

        result = http_client.get(
            url=url, service="billcom", headers={"Authorization": f"Bearer {cred['access_token']}"}
        )

        return {
            "vendors": [
                {
                    "vendor_id": f"bc:{v['id']}",
                    "vendor_name": v.get("name"),
                    "email": v.get("email"),
                    "status": v.get("status"),
                }
                for v in result.get("vendors", [])
            ],
            "total": result.get("total", 0),
        }

    def get_payment_status(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get payment status from Bill.com"""
        cred = self._get_access_token(org_id, user_id)

        payment_id = args.get("payment_id", "").replace("bc:", "")

        url = f"{self.base_url}/payments/{payment_id}"
        result = http_client.get(
            url=url, service="billcom", headers={"Authorization": f"Bearer {cred['access_token']}"}
        )

        return {
            "payment_id": f"bc:{result['id']}",
            "amount": result.get("amount"),
            "status": result.get("status"),
            "payment_method": result.get("paymentMethod"),
            "process_date": result.get("processDate"),
            "vendor_name": result.get("vendorName"),
        }

    def create_vendor_credit(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a vendor credit in Bill.com"""
        cred = self._get_access_token(org_id, user_id)

        vendor_id = args.get("vendor_id", "").replace("bc:", "")

        credit_data = {
            "vendorId": vendor_id,
            "creditDate": args.get("credit_date", datetime.now().strftime("%Y-%m-%d")),
            "amount": args.get("amount"),
            "description": args.get("description", ""),
        }

        url = f"{self.base_url}/vendorCredits"
        result = http_client.post(
            url=url,
            service="billcom",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json=credit_data,
        )

        return {
            "credit_id": f"bc:{result['id']}",
            "vendor_id": f"bc:{vendor_id}",
            "amount": result.get("amount"),
            "status": result.get("status"),
        }

    def approve_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Approve a bill in Bill.com"""
        cred = self._get_access_token(org_id, user_id)

        bill_id = args.get("bill_id", "").replace("bc:", "")

        approval_data = {"status": "APPROVED", "approverNotes": args.get("notes", "")}

        url = f"{self.base_url}/bills/{bill_id}/approve"
        result = http_client.post(
            url=url,
            service="billcom",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
            },
            json=approval_data,
        )

        return {
            "bill_id": f"bc:{bill_id}",
            "status": result.get("status"),
            "approved_at": result.get("approvedAt"),
            "approved_by": result.get("approvedBy"),
        }
