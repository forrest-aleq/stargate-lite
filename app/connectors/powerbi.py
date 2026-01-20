"""
Power BI connector for Stargate Lite
Handles datasets, reports, dashboards, workspaces, embed tokens
Uses Power BI REST API v1.0 (October 2025)
"""

import os
from typing import Any, cast

import requests

from app.logging_config import get_logger

logger = get_logger(__name__)


class PowerBIConnector:
    """Power BI REST API connector for business intelligence"""

    BASE_URL = "https://api.powerbi.com/v1.0/myorg"

    def __init__(self) -> None:
        self.client_id = os.getenv("POWERBI_CLIENT_ID")
        self.client_secret = os.getenv("POWERBI_CLIENT_SECRET")
        self.tenant_id = os.getenv("POWERBI_TENANT_ID")

    def _get_access_token(self, args: dict[str, Any]) -> str:
        """Extract and validate access_token from args."""
        access_token = args.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise ValueError("access_token is required and must be a string")
        return access_token

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    def _make_request(
        self, method: str, endpoint: str, access_token: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers(access_token)

        if method == "GET":
            response = requests.get(url, headers=headers, params=data, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")

        # Some operations return 200, others 202 (accepted), or 204 (no content)
        if response.status_code not in [200, 201, 202, 204]:
            raise Exception(f"Power BI API error: {response.status_code} - {response.text}")

        # 204 No Content returns empty response
        if response.status_code == 204:
            return {"status": "success"}

        if not response.text:
            return {"status": "success"}

        return cast(dict[str, Any], response.json())

    def list_datasets(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all datasets in workspace"""
        access_token = self._get_access_token(args)
        workspace_id = args.get("workspace_id")

        # If workspace_id provided, get datasets in that workspace
        if workspace_id:
            endpoint = f"/groups/{workspace_id}/datasets"
        else:
            endpoint = "/datasets"

        result = self._make_request("GET", endpoint, access_token)

        return {
            "datasets": [
                {
                    "dataset_id": ds["id"],
                    "name": ds.get("name"),
                    "configured_by": ds.get("configuredBy"),
                    "is_refreshable": ds.get("isRefreshable"),
                    "is_effective_identity_required": ds.get("isEffectiveIdentityRequired"),
                    "web_url": ds.get("webUrl"),
                }
                for ds in result.get("value", [])
            ]
        }

    def get_dataset(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get dataset details"""
        access_token = self._get_access_token(args)
        dataset_id = args.get("dataset_id")
        workspace_id = args.get("workspace_id")

        if workspace_id:
            endpoint = f"/groups/{workspace_id}/datasets/{dataset_id}"
        else:
            endpoint = f"/datasets/{dataset_id}"

        result = self._make_request("GET", endpoint, access_token)

        return {
            "dataset_id": result["id"],
            "name": result.get("name"),
            "configured_by": result.get("configuredBy"),
            "is_refreshable": result.get("isRefreshable"),
            "tables": result.get("tables", []),
            "web_url": result.get("webUrl"),
        }

    def refresh_dataset(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Trigger a dataset refresh"""
        access_token = self._get_access_token(args)
        dataset_id = args.get("dataset_id")
        workspace_id = args.get("workspace_id")

        # Optional parameters for refresh
        refresh_data = {}
        if args.get("notify_option"):
            refresh_data["notifyOption"] = args["notify_option"]  # NoNotification or MailOnFailure

        if workspace_id:
            endpoint = f"/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        else:
            endpoint = f"/datasets/{dataset_id}/refreshes"

        self._make_request("POST", endpoint, access_token, refresh_data)

        return {
            "dataset_id": dataset_id,
            "status": "refresh_triggered",
            "message": "Dataset refresh has been queued",
        }

    def list_reports(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all reports in workspace"""
        access_token = self._get_access_token(args)
        workspace_id = args.get("workspace_id")

        if workspace_id:
            endpoint = f"/groups/{workspace_id}/reports"
        else:
            endpoint = "/reports"

        result = self._make_request("GET", endpoint, access_token)

        return {
            "reports": [
                {
                    "report_id": r["id"],
                    "name": r.get("name"),
                    "dataset_id": r.get("datasetId"),
                    "embed_url": r.get("embedUrl"),
                    "web_url": r.get("webUrl"),
                }
                for r in result.get("value", [])
            ]
        }

    def get_report(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get report details"""
        access_token = self._get_access_token(args)
        report_id = args.get("report_id")
        workspace_id = args.get("workspace_id")

        if workspace_id:
            endpoint = f"/groups/{workspace_id}/reports/{report_id}"
        else:
            endpoint = f"/reports/{report_id}"

        result = self._make_request("GET", endpoint, access_token)

        return {
            "report_id": result["id"],
            "name": result.get("name"),
            "dataset_id": result.get("datasetId"),
            "embed_url": result.get("embedUrl"),
            "web_url": result.get("webUrl"),
            "report_type": result.get("reportType"),
        }

    def export_report(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Export report to file (PDF, PPTX, PNG)"""
        access_token = self._get_access_token(args)
        report_id = args.get("report_id")
        workspace_id = args.get("workspace_id")
        file_format = args.get("format", "PDF")  # PDF, PPTX, PNG

        export_data = {"format": file_format}

        # Optional: specific pages or bookmarks
        if args.get("pages"):
            export_data["powerBIReportConfiguration"] = {"pages": args["pages"]}

        if workspace_id:
            endpoint = f"/groups/{workspace_id}/reports/{report_id}/ExportTo"
        else:
            endpoint = f"/reports/{report_id}/ExportTo"

        result = self._make_request("POST", endpoint, access_token, export_data)

        return {
            "export_id": result.get("id"),
            "status": result.get("status"),
            "report_id": report_id,
            "format": file_format,
            "message": "Export job created. Use export_id to check status and download.",
        }

    def list_dashboards(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all dashboards in workspace"""
        access_token = self._get_access_token(args)
        workspace_id = args.get("workspace_id")

        if workspace_id:
            endpoint = f"/groups/{workspace_id}/dashboards"
        else:
            endpoint = "/dashboards"

        result = self._make_request("GET", endpoint, access_token)

        return {
            "dashboards": [
                {
                    "dashboard_id": d["id"],
                    "name": d.get("displayName"),
                    "is_read_only": d.get("isReadOnly"),
                    "embed_url": d.get("embedUrl"),
                    "web_url": d.get("webUrl"),
                }
                for d in result.get("value", [])
            ]
        }

    def get_dashboard(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get dashboard details"""
        access_token = self._get_access_token(args)
        dashboard_id = args.get("dashboard_id")
        workspace_id = args.get("workspace_id")

        if workspace_id:
            endpoint = f"/groups/{workspace_id}/dashboards/{dashboard_id}"
        else:
            endpoint = f"/dashboards/{dashboard_id}"

        result = self._make_request("GET", endpoint, access_token)

        return {
            "dashboard_id": result["id"],
            "name": result.get("displayName"),
            "is_read_only": result.get("isReadOnly"),
            "embed_url": result.get("embedUrl"),
            "web_url": result.get("webUrl"),
        }

    def generate_embed_token(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate embed token for reports/dashboards"""
        access_token = self._get_access_token(args)
        workspace_id = args.get("workspace_id")

        # Embed token can be for reports, datasets, or dashboards
        token_data = {
            "datasets": args.get("datasets", []),  # Array of {id: "dataset_id"}
            "reports": args.get("reports", []),  # Array of {id: "report_id"}
            "targetWorkspaces": args.get("target_workspaces", []),  # Optional
        }

        # Optional: identity information for RLS (Row-Level Security)
        if args.get("identities"):
            token_data["identities"] = args["identities"]

        if workspace_id:
            endpoint = f"/groups/{workspace_id}/GenerateToken"
        else:
            endpoint = "/GenerateToken"

        result = self._make_request("POST", endpoint, access_token, token_data)

        return {
            "embed_token": result.get("token"),
            "token_id": result.get("tokenId"),
            "expiration": result.get("expiration"),
        }

    def create_workspace(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new workspace (group)"""
        access_token = self._get_access_token(args)

        workspace_data = {"name": args.get("workspace_name")}

        # Optional: capacity assignment
        if args.get("capacity_id"):
            workspace_data["capacityId"] = args["capacity_id"]

        result = self._make_request("POST", "/groups", access_token, workspace_data)

        return {
            "workspace_id": result.get("id"),
            "name": result.get("name"),
            "is_read_only": result.get("isReadOnly"),
            "is_on_dedicated_capacity": result.get("isOnDedicatedCapacity"),
        }
