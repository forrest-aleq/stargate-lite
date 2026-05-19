"""
Google Sheets connector for Stargate Lite
Handles spreadsheet operations via Sheets API v4
Shares OAuth credentials with Gmail/Drive/Calendar (service="google")
"""

import os
from typing import Any, ClassVar

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)


class GoogleSheetsConnector:
    """Google Sheets API connector"""

    # Combined scopes for all Google services
    SCOPES: ClassVar[list[str]] = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    def __init__(self) -> None:
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    def _get_credentials(self, org_id: str, user_id: str) -> Credentials:
        """Get valid Google credentials (shared with Gmail/Drive/Calendar)."""
        cred_data = CredentialManager.get_credential(org_id, user_id, "google")

        if not cred_data:
            raise ValueError(f"No Google credentials found for org_id={org_id}, user_id={user_id}")

        creds = Credentials(
            token=cred_data["access_token"],
            refresh_token=cred_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.SCOPES,
        )

        # Refresh if needed
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                logger.info(
                    "Google token expired, refreshing",
                    service="google_sheets",
                    org_id=org_id,
                    user_id=user_id,
                    log_event="token_refresh_start",
                )
                try:
                    creds.refresh(Request())

                    # Store the refreshed token
                    CredentialManager.store_credential(
                        org_id=org_id,
                        user_id=user_id,
                        service="google",
                        access_token=creds.token,
                        refresh_token=creds.refresh_token,
                        token_expiry=creds.expiry,
                    )
                    logger.info(
                        "Google token refreshed successfully",
                        service="google_sheets",
                        org_id=org_id,
                        user_id=user_id,
                        log_event="token_refresh_success",
                    )
                except Exception as e:
                    logger.error(
                        "Google token refresh failed",
                        service="google_sheets",
                        org_id=org_id,
                        user_id=user_id,
                        error_type=type(e).__name__,
                        log_event="token_refresh_error",
                        exc_info=True,
                    )
                    raise

        return creds

    def get_range(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get values from a range in a Google Sheet"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("sheets", "v4", credentials=creds)

            spreadsheet_id = args.get("spreadsheet_id")
            range_name = args.get("range")  # e.g., "Sheet1!A1:D10"

            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )

            values = result.get("values", [])

            return {
                "spreadsheet_id": spreadsheet_id,
                "range": result.get("range"),
                "values": values,
                "row_count": len(values),
                "column_count": len(values[0]) if values else 0,
            }

        except HttpError as error:
            raise Exception(f"Google Sheets API error: {error}") from error

    def update_range(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update values in a range in a Google Sheet"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("sheets", "v4", credentials=creds)

            spreadsheet_id = args.get("spreadsheet_id")
            range_name = args.get("range")  # e.g., "Sheet1!A1:D10"
            values = args.get("values")  # 2D array of values

            body = {"values": values}

            result = (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",  # Parse formulas, dates, etc.
                    body=body,
                )
                .execute()
            )

            return {
                "spreadsheet_id": spreadsheet_id,
                "updated_range": result.get("updatedRange"),
                "updated_rows": result.get("updatedRows"),
                "updated_columns": result.get("updatedColumns"),
                "updated_cells": result.get("updatedCells"),
                "status": "updated",
            }

        except HttpError as error:
            raise Exception(f"Google Sheets API error: {error}") from error

    def append_row(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Append a row to a Google Sheet"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("sheets", "v4", credentials=creds)

            spreadsheet_id = args.get("spreadsheet_id")
            range_name = args.get("range")  # e.g., "Sheet1!A:D" (column range)
            values = args.get("values")  # Single row as array

            if not isinstance(values, list) or len(values) == 0:
                raise ValueError("values is required and must be a non-empty list")

            is_simple = isinstance(values[0], str | int | float)
            body = {"values": [values] if is_simple else values}

            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )

            return {
                "spreadsheet_id": spreadsheet_id,
                "updated_range": result.get("updates", {}).get("updatedRange"),
                "updated_rows": result.get("updates", {}).get("updatedRows"),
                "updated_cells": result.get("updates", {}).get("updatedCells"),
                "status": "appended",
            }

        except HttpError as error:
            raise Exception(f"Google Sheets API error: {error}") from error

    def create_sheet(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new sheet (tab) in a Google Spreadsheet"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("sheets", "v4", credentials=creds)

            spreadsheet_id = args.get("spreadsheet_id")
            sheet_title = args.get("sheet_title")

            body = {"requests": [{"addSheet": {"properties": {"title": sheet_title}}}]}

            result = (
                service.spreadsheets()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                .execute()
            )

            sheet_id = result["replies"][0]["addSheet"]["properties"]["sheetId"]

            return {
                "spreadsheet_id": spreadsheet_id,
                "sheet_id": sheet_id,
                "sheet_title": sheet_title,
                "status": "created",
            }

        except HttpError as error:
            raise Exception(f"Google Sheets API error: {error}") from error

    def batch_update(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Perform batch updates on a Google Spreadsheet (values and/or structure)"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("sheets", "v4", credentials=creds)

            spreadsheet_id = args.get("spreadsheet_id")
            requests = args.get("requests")  # List of update requests

            body = {"requests": requests}

            result = (
                service.spreadsheets()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                .execute()
            )

            return {
                "spreadsheet_id": spreadsheet_id,
                "replies_count": len(result.get("replies", [])),
                "updated_spreadsheet": result.get("spreadsheetId"),
                "status": "batch_updated",
            }

        except HttpError as error:
            raise Exception(f"Google Sheets API error: {error}") from error

    def clear_range(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Clear values in a range in a Google Sheet"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("sheets", "v4", credentials=creds)

            spreadsheet_id = args.get("spreadsheet_id")
            range_name = args.get("range")  # e.g., "Sheet1!A1:D10"

            result = (
                service.spreadsheets()
                .values()
                .clear(spreadsheetId=spreadsheet_id, range=range_name, body={})
                .execute()
            )

            return {
                "spreadsheet_id": spreadsheet_id,
                "cleared_range": result.get("clearedRange"),
                "status": "cleared",
            }

        except HttpError as error:
            raise Exception(f"Google Sheets API error: {error}") from error

    def get_sheet_metadata(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get metadata about a Google Spreadsheet (sheets, properties, etc.)"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("sheets", "v4", credentials=creds)

            spreadsheet_id = args.get("spreadsheet_id")

            result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

            return {
                "spreadsheet_id": result.get("spreadsheetId"),
                "title": result.get("properties", {}).get("title"),
                "locale": result.get("properties", {}).get("locale"),
                "timezone": result.get("properties", {}).get("timeZone"),
                "sheets": [
                    {
                        "sheet_id": sheet["properties"]["sheetId"],
                        "title": sheet["properties"]["title"],
                        "index": sheet["properties"]["index"],
                        "row_count": sheet["properties"].get("gridProperties", {}).get("rowCount"),
                        "column_count": (
                            sheet["properties"].get("gridProperties", {}).get("columnCount")
                        ),
                    }
                    for sheet in result.get("sheets", [])
                ],
            }

        except HttpError as error:
            raise Exception(f"Google Sheets API error: {error}") from error

    def batch_get_ranges(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get values from multiple ranges in a Google Sheet"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("sheets", "v4", credentials=creds)

            spreadsheet_id = args.get("spreadsheet_id")
            ranges = args.get("ranges", [])  # e.g., ["Sheet1!A1:B5", "Sheet2!C1:D10"]

            result = (
                service.spreadsheets()
                .values()
                .batchGet(spreadsheetId=spreadsheet_id, ranges=ranges)
                .execute()
            )

            value_ranges = result.get("valueRanges", [])
            return {
                "spreadsheet_id": spreadsheet_id,
                "ranges": [
                    {
                        "range": vr.get("range"),
                        "values": vr.get("values", []),
                    }
                    for vr in value_ranges
                ],
                "count": len(value_ranges),
            }

        except HttpError as error:
            raise Exception(f"Google Sheets API error: {error}") from error

    def create_spreadsheet(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new Google Spreadsheet"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("sheets", "v4", credentials=creds)

            spreadsheet_body: dict[str, Any] = {
                "properties": {"title": args.get("title", "Untitled Spreadsheet")},
            }

            if args.get("sheet_titles"):
                spreadsheet_body["sheets"] = [
                    {"properties": {"title": title}} for title in args["sheet_titles"]
                ]

            result = service.spreadsheets().create(body=spreadsheet_body).execute()

            return {
                "spreadsheet_id": result.get("spreadsheetId"),
                "title": result.get("properties", {}).get("title"),
                "url": result.get("spreadsheetUrl"),
                "sheets": [
                    {
                        "sheet_id": sheet["properties"]["sheetId"],
                        "title": sheet["properties"]["title"],
                    }
                    for sheet in result.get("sheets", [])
                ],
            }

        except HttpError as error:
            raise Exception(f"Google Sheets API error: {error}") from error
