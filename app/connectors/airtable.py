"""
Airtable connector for Stargate Lite
Handles bases, tables, records, fields, and webhooks
Uses Airtable Web API
"""

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from app.database import CredentialManager
from app.errors import CredentialMissingError
from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class AirtableConnector:
    """Airtable Web API connector"""

    BASE_URL = "https://api.airtable.com/v0"
    META_URL = "https://api.airtable.com/v0/meta"

    def __init__(self) -> None:
        pass

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token"""
        cred = CredentialManager.get_credential(org_id, user_id, "airtable")

        if not cred:
            raise CredentialMissingError("airtable", org_id, user_id)

        # Airtable OAuth tokens can expire - check and refresh if needed
        if cred.get("token_expiry") and cred["token_expiry"] < datetime.utcnow() + timedelta(minutes=5):
            logger.info("Token expired, refreshing", service="airtable", org_id=org_id)
            return self._refresh_token(org_id, user_id, cred["refresh_token"])

        return cred

    def _refresh_token(self, org_id: str, user_id: str, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token"""
        import os

        client_id = os.getenv("AIRTABLE_CLIENT_ID")
        client_secret = os.getenv("AIRTABLE_CLIENT_SECRET")

        token_data = http_client.post(
            url="https://airtable.com/oauth2/v1/token",
            service="airtable",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )

        new_expiry = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))

        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="airtable",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", refresh_token),
            token_expiry=new_expiry,
        )

        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", refresh_token),
            "token_expiry": new_expiry,
        }

    # ============ BASES ============

    def list_bases(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List bases accessible to the user"""
        cred = self._get_access_token(org_id, user_id)

        params = {}
        if args.get("offset"):
            params["offset"] = args["offset"]

        url = f"{self.META_URL}/bases"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
        )

        bases = result.get("bases", [])
        return {
            "bases": [
                {
                    "id": b["id"],
                    "name": b.get("name"),
                    "permission_level": b.get("permissionLevel"),
                }
                for b in bases
            ],
            "offset": result.get("offset"),
        }

    # ============ TABLES ============

    def list_tables(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List tables in a base"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]

        result = http_client.get(
            url=f"{self.META_URL}/bases/{base_id}/tables",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
        )

        tables = result.get("tables", [])
        return {
            "tables": [
                {
                    "id": t["id"],
                    "name": t.get("name"),
                    "primary_field_id": t.get("primaryFieldId"),
                    "fields": t.get("fields", []),
                    "views": t.get("views", []),
                }
                for t in tables
            ],
        }

    def create_table(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new table in a base"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]

        table_data: dict[str, Any] = {
            "name": args["name"],
            "fields": args["fields"],
        }
        if args.get("description"):
            table_data["description"] = args["description"]

        result = http_client.post(
            url=f"{self.META_URL}/bases/{base_id}/tables",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
            json=table_data,
        )

        return {
            "id": result["id"],
            "name": result.get("name"),
            "primary_field_id": result.get("primaryFieldId"),
            "fields": result.get("fields", []),
        }

    # ============ RECORDS ============

    def list_records(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List records from an Airtable table"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]
        table_id = args["table_id"]

        params: dict[str, Any] = {}
        if args.get("view"):
            params["view"] = args["view"]
        if args.get("fields"):
            # Airtable uses fields[] parameter for multiple fields
            for field in args["fields"]:
                params.setdefault("fields[]", []).append(field)
        if args.get("filter_by_formula"):
            params["filterByFormula"] = args["filter_by_formula"]
        if args.get("sort"):
            for i, sort_spec in enumerate(args["sort"]):
                params[f"sort[{i}][field]"] = sort_spec["field"]
                if "direction" in sort_spec:
                    params[f"sort[{i}][direction]"] = sort_spec["direction"]
        if args.get("max_records"):
            params["maxRecords"] = args["max_records"]
        if args.get("page_size"):
            params["pageSize"] = min(args["page_size"], 100)
        if args.get("offset"):
            params["offset"] = args["offset"]

        url = f"{self.BASE_URL}/{base_id}/{table_id}"
        if params:
            # Handle array params specially
            param_parts = []
            for k, v in params.items():
                if isinstance(v, list):
                    for item in v:
                        param_parts.append(f"{k}={item}")
                else:
                    param_parts.append(f"{k}={v}")
            url += "?" + "&".join(param_parts)

        result = http_client.get(
            url=url,
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
        )

        records = result.get("records", [])
        return {
            "records": [
                {
                    "id": r["id"],
                    "created_time": r.get("createdTime"),
                    "fields": r.get("fields", {}),
                }
                for r in records
            ],
            "offset": result.get("offset"),
        }

    def get_record(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific record from Airtable"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]
        table_id = args["table_id"]
        record_id = args["record_id"]

        result = http_client.get(
            url=f"{self.BASE_URL}/{base_id}/{table_id}/{record_id}",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "id": result["id"],
            "created_time": result.get("createdTime"),
            "fields": result.get("fields", {}),
        }

    def create_records(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create record(s) in Airtable"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]
        table_id = args["table_id"]

        request_data: dict[str, Any] = {
            "records": args["records"],
        }
        if args.get("typecast"):
            request_data["typecast"] = True

        result = http_client.post(
            url=f"{self.BASE_URL}/{base_id}/{table_id}",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
            json=request_data,
        )

        records = result.get("records", [])
        return {
            "records": [
                {
                    "id": r["id"],
                    "created_time": r.get("createdTime"),
                    "fields": r.get("fields", {}),
                }
                for r in records
            ],
        }

    def update_records(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update record(s) in Airtable"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]
        table_id = args["table_id"]

        request_data: dict[str, Any] = {
            "records": args["records"],
        }
        if args.get("typecast"):
            request_data["typecast"] = True

        # PATCH for partial update (default), PUT would replace all fields
        result = http_client.patch(
            url=f"{self.BASE_URL}/{base_id}/{table_id}",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
            json=request_data,
        )

        records = result.get("records", [])
        return {
            "records": [
                {
                    "id": r["id"],
                    "created_time": r.get("createdTime"),
                    "fields": r.get("fields", {}),
                }
                for r in records
            ],
        }

    def delete_records(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete record(s) from Airtable"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]
        table_id = args["table_id"]
        record_ids = args["record_ids"]

        # Airtable delete uses query params for record IDs
        params = "&".join([f"records[]={rid}" for rid in record_ids])
        url = f"{self.BASE_URL}/{base_id}/{table_id}?{params}"

        result = http_client.delete(
            url=url,
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
        )

        records = result.get("records", [])
        return {
            "records": [
                {
                    "id": r["id"],
                    "deleted": r.get("deleted", True),
                }
                for r in records
            ],
        }

    # ============ FIELDS ============

    def create_field(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new field in an Airtable table"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]
        table_id = args["table_id"]

        field_data: dict[str, Any] = {
            "name": args["name"],
            "type": args["type"],
        }
        if args.get("options"):
            field_data["options"] = args["options"]
        if args.get("description"):
            field_data["description"] = args["description"]

        result = http_client.post(
            url=f"{self.META_URL}/bases/{base_id}/tables/{table_id}/fields",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
            json=field_data,
        )

        return {
            "id": result["id"],
            "name": result.get("name"),
            "type": result.get("type"),
        }

    def update_field(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a field's name or description"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]
        table_id = args["table_id"]
        field_id = args["field_id"]

        field_data: dict[str, Any] = {}
        if args.get("name"):
            field_data["name"] = args["name"]
        if args.get("description"):
            field_data["description"] = args["description"]

        result = http_client.patch(
            url=f"{self.META_URL}/bases/{base_id}/tables/{table_id}/fields/{field_id}",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
            json=field_data,
        )

        return {
            "id": result["id"],
            "name": result.get("name"),
            "type": result.get("type"),
            "description": result.get("description"),
        }

    # ============ WEBHOOKS ============

    def list_webhooks(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List webhooks for a base"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]

        result = http_client.get(
            url=f"{self.BASE_URL}/bases/{base_id}/webhooks",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
        )

        webhooks = result.get("webhooks", [])
        return {
            "webhooks": [
                {
                    "id": w["id"],
                    "notification_url": w.get("notificationUrl"),
                    "specification": w.get("specification"),
                    "cursor_for_next_payload": w.get("cursorForNextPayload"),
                    "is_hook_enabled": w.get("isHookEnabled"),
                    "expiration_time": w.get("expirationTime"),
                }
                for w in webhooks
            ],
        }

    def create_webhook(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a webhook for record changes"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]

        webhook_data = {
            "notificationUrl": args["notification_url"],
            "specification": args["specification"],
        }

        result = http_client.post(
            url=f"{self.BASE_URL}/bases/{base_id}/webhooks",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
            json=webhook_data,
        )

        return {
            "id": result["id"],
            "mac_secret_base64": result.get("macSecretBase64"),
            "expiration_time": result.get("expirationTime"),
        }

    def delete_webhook(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a webhook"""
        cred = self._get_access_token(org_id, user_id)
        base_id = args["base_id"]
        webhook_id = args["webhook_id"]

        http_client.delete(
            url=f"{self.BASE_URL}/bases/{base_id}/webhooks/{webhook_id}",
            service="airtable",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "deleted": True,
        }


# Singleton instance
airtable_connector = AirtableConnector()
