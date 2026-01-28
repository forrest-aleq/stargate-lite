"""
Microsoft Excel connector for Stargate Lite
Handles Excel workbook operations via Microsoft Graph API
Uses OAuth 2.0 with delegated permissions (user impersonation per architecture decision)
Shares OAuth credentials with OneDrive and Outlook Calendar (service="microsoft")
"""

import os
from datetime import datetime, timedelta
from typing import Any, ClassVar, cast

import requests

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)


def _column_number_to_letter(col_num: int) -> str:
    """Convert 1-based column number to Excel column letter(s).

    Examples: 1 -> A, 26 -> Z, 27 -> AA, 52 -> AZ, 703 -> AAA
    """
    result = ""
    while col_num > 0:
        col_num, remainder = divmod(col_num - 1, 26)
        result = chr(65 + remainder) + result
    return result


class MicrosoftExcelConnector:
    """Microsoft Graph API Excel connector"""

    # Combined scopes for all Microsoft services (Excel, OneDrive, Calendar)
    SCOPES: ClassVar[list[str]] = [
        "https://graph.microsoft.com/Files.ReadWrite.All",  # OneDrive/Excel
        "https://graph.microsoft.com/Calendars.ReadWrite",  # Outlook Calendar
        "https://graph.microsoft.com/Mail.ReadWrite",  # Outlook Mail
        "offline_access",  # Required for refresh tokens
    ]

    def __init__(self) -> None:
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.graph_url = "https://graph.microsoft.com/v1.0"

    def _get_access_token(self, org_id: str, user_id: str) -> str:
        """Get valid access token, refreshing if necessary"""
        cred_data = CredentialManager.get_credential(org_id, user_id, "microsoft")

        if not cred_data:
            raise ValueError(
                f"No Microsoft credentials found for org_id={org_id}, user_id={user_id}"
            )

        # Check if token is expired (within 5 minutes)
        expiry = cred_data.get("token_expiry")
        if expiry and datetime.fromisoformat(expiry) < datetime.now() + timedelta(minutes=5):
            logger.info(
                "Microsoft token expired or expiring soon, refreshing",
                service="microsoft_excel",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_start",
            )
            try:
                # Refresh token
                token_response = requests.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": cred_data["refresh_token"],
                        "grant_type": "refresh_token",
                        "scope": " ".join(self.SCOPES),
                    },
                    timeout=30,
                )

                if token_response.status_code != 200:
                    raise Exception(f"Token refresh failed: {token_response.text}")

                token_data = token_response.json()

                # Store refreshed token
                new_expiry = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))
                CredentialManager.store_credential(
                    org_id=org_id,
                    user_id=user_id,
                    service="microsoft",
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token", cred_data["refresh_token"]),
                    token_expiry=new_expiry,
                )

                logger.info(
                    "Microsoft token refreshed successfully",
                    service="microsoft_excel",
                    org_id=org_id,
                    user_id=user_id,
                    expires_in_seconds=token_data.get("expires_in", 3600),
                    log_event="token_refresh_success",
                )

                return str(token_data["access_token"])
            except Exception as e:
                logger.error(
                    "Microsoft token refresh failed",
                    service="microsoft_excel",
                    org_id=org_id,
                    user_id=user_id,
                    error_type=type(e).__name__,
                    log_event="token_refresh_error",
                    exc_info=True,
                )
                raise

        return str(cred_data["access_token"])

    def _make_request(
        self, method: str, endpoint: str, token: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make authenticated request to Microsoft Graph API"""
        url = f"{self.graph_url}/{endpoint}"

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if response.status_code not in [200, 201, 204]:
            raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")

        if response.status_code == 204:
            return {"status": "success"}

        return cast(dict[str, Any], response.json())

    def get_range(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get values from a range in an Excel workbook"""
        token = self._get_access_token(org_id, user_id)

        workbook_id = args.get("workbook_id")  # Drive item ID of Excel file
        worksheet_name = args.get("worksheet_name", "Sheet1")
        range_address = args.get("range")  # e.g., "A1:D10"

        endpoint = (
            f"me/drive/items/{workbook_id}/workbook/worksheets/"
            f"{worksheet_name}/range(address='{range_address}')"
        )

        result = self._make_request("GET", endpoint, token)

        return {
            "workbook_id": workbook_id,
            "worksheet": worksheet_name,
            "range": result.get("address"),
            "values": result.get("values", []),
            "row_count": result.get("rowCount"),
            "column_count": result.get("columnCount"),
        }

    def update_range(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update values in a range in an Excel workbook"""
        token = self._get_access_token(org_id, user_id)

        workbook_id = args.get("workbook_id")
        worksheet_name = args.get("worksheet_name", "Sheet1")
        range_address = args.get("range")  # e.g., "A1:D10"
        values = args.get("values")  # 2D array of values

        endpoint = (
            f"me/drive/items/{workbook_id}/workbook/worksheets/"
            f"{worksheet_name}/range(address='{range_address}')"
        )

        data = {"values": values}

        result = self._make_request("PATCH", endpoint, token, data)

        return {
            "workbook_id": workbook_id,
            "worksheet": worksheet_name,
            "updated_range": result.get("address"),
            "status": "updated",
        }

    def append_row(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Append a row to an Excel worksheet"""
        token = self._get_access_token(org_id, user_id)

        workbook_id = args.get("workbook_id")
        worksheet_name = args.get("worksheet_name", "Sheet1")
        values = args.get("values")  # Single row as array

        if not isinstance(values, list):
            raise ValueError("values is required and must be a list")

        # First, get the used range to find the next empty row
        endpoint_used = (
            f"me/drive/items/{workbook_id}/workbook/worksheets/{worksheet_name}/usedRange"
        )
        used_range = self._make_request("GET", endpoint_used, token)

        next_row = used_range.get("rowCount", 0) + 1

        # Determine column range (e.g., if values has 4 items, use A:D; 27 items uses A:AA)
        num_cols = len(values)
        col_end = _column_number_to_letter(num_cols)
        range_address = f"A{next_row}:{col_end}{next_row}"

        # Update the range
        endpoint_update = (
            f"me/drive/items/{workbook_id}/workbook/worksheets/"
            f"{worksheet_name}/range(address='{range_address}')"
        )

        data = {"values": [values]}

        result = self._make_request("PATCH", endpoint_update, token, data)

        return {
            "workbook_id": workbook_id,
            "worksheet": worksheet_name,
            "appended_range": result.get("address"),
            "status": "appended",
        }

    def create_worksheet(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new worksheet in an Excel workbook"""
        token = self._get_access_token(org_id, user_id)

        workbook_id = args.get("workbook_id")
        worksheet_name = args.get("worksheet_name")

        endpoint = f"me/drive/items/{workbook_id}/workbook/worksheets/add"

        data = {"name": worksheet_name}

        result = self._make_request("POST", endpoint, token, data)

        return {
            "workbook_id": workbook_id,
            "worksheet_id": result.get("id"),
            "worksheet_name": result.get("name"),
            "status": "created",
        }

    def get_worksheets(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all worksheets in an Excel workbook"""
        token = self._get_access_token(org_id, user_id)

        workbook_id = args.get("workbook_id")

        endpoint = f"me/drive/items/{workbook_id}/workbook/worksheets"

        result = self._make_request("GET", endpoint, token)

        worksheets = result.get("value", [])

        return {
            "workbook_id": workbook_id,
            "worksheets": [
                {
                    "id": ws.get("id"),
                    "name": ws.get("name"),
                    "position": ws.get("position"),
                    "visibility": ws.get("visibility"),
                }
                for ws in worksheets
            ],
            "count": len(worksheets),
        }

    def create_table(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a table in an Excel worksheet"""
        token = self._get_access_token(org_id, user_id)

        workbook_id = args.get("workbook_id")
        worksheet_name = args.get("worksheet_name", "Sheet1")
        range_address = args.get("range")  # e.g., "A1:D10"
        has_headers = args.get("has_headers", True)

        endpoint = f"me/drive/items/{workbook_id}/workbook/worksheets/{worksheet_name}/tables/add"

        data = {"address": range_address, "hasHeaders": has_headers}

        result = self._make_request("POST", endpoint, token, data)

        return {
            "workbook_id": workbook_id,
            "worksheet": worksheet_name,
            "table_id": result.get("id"),
            "table_name": result.get("name"),
            "status": "created",
        }
