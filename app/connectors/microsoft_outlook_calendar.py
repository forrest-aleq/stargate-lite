"""
Microsoft Outlook Calendar connector for Stargate Lite
Handles calendar event management via Microsoft Graph API
Uses delegated permissions to impersonate user (Option B per architecture decision)
Shares OAuth credentials with Excel and OneDrive (service="microsoft")
"""

import os
from datetime import datetime, timedelta
from typing import Any, ClassVar, cast

import requests

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)


class MicrosoftOutlookCalendarConnector:
    """Microsoft Graph API Outlook Calendar connector"""

    # Combined scopes for all Microsoft services
    SCOPES: ClassVar[list[str]] = [
        "https://graph.microsoft.com/Files.ReadWrite.All",
        "https://graph.microsoft.com/Calendars.ReadWrite",
        "https://graph.microsoft.com/Mail.ReadWrite",
        "offline_access",
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

        # Check if token is expired
        expiry = cred_data.get("token_expiry")
        if expiry and datetime.fromisoformat(expiry) < datetime.now() + timedelta(minutes=5):
            logger.info(
                "Microsoft token expired or expiring soon, refreshing",
                service="microsoft_outlook_calendar",
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
                    service="microsoft_outlook_calendar",
                    org_id=org_id,
                    user_id=user_id,
                    expires_in_seconds=token_data.get("expires_in", 3600),
                    log_event="token_refresh_success",
                )

                return str(token_data["access_token"])
            except Exception as e:
                logger.error(
                    "Microsoft token refresh failed",
                    service="microsoft_outlook_calendar",
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

    def create_event(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a calendar event (impersonating user)"""
        token = self._get_access_token(org_id, user_id)

        event = {
            "subject": args.get("subject"),
            "body": {
                "contentType": "HTML" if args.get("is_html") else "Text",
                "content": args.get("body", ""),
            },
            "start": {
                "dateTime": args.get("start_datetime"),  # ISO 8601 format
                "timeZone": args.get("timezone", "Eastern Standard Time"),
            },
            "end": {
                "dateTime": args.get("end_datetime"),  # ISO 8601 format
                "timeZone": args.get("timezone", "Eastern Standard Time"),
            },
        }

        # Add attendees if provided
        if args.get("attendees"):
            event["attendees"] = [
                {"emailAddress": {"address": attendee}, "type": "required"}
                for attendee in args["attendees"]
            ]

        # Add location if provided
        if args.get("location"):
            event["location"] = {"displayName": args["location"]}

        # Add Teams meeting if requested
        if args.get("add_teams_meeting"):
            event["isOnlineMeeting"] = True
            event["onlineMeetingProvider"] = "teamsForBusiness"

        endpoint = "me/events"

        result = self._make_request("POST", endpoint, token, event)

        return {
            "event_id": result.get("id"),
            "subject": result.get("subject"),
            "start_time": result["start"].get("dateTime"),
            "end_time": result["end"].get("dateTime"),
            "web_link": result.get("webLink"),
            "teams_link": (
                result.get("onlineMeeting", {}).get("joinUrl")
                if result.get("isOnlineMeeting")
                else None
            ),
            "status": "confirmed",
            "attendees": [
                {
                    "email": att["emailAddress"].get("address"),
                    "response_status": att.get("status", {}).get("response"),
                }
                for att in result.get("attendees", [])
            ],
        }

    def check_availability(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Check free/busy schedule for attendees"""
        token = self._get_access_token(org_id, user_id)

        attendee_emails = args.get("attendees", [])
        start_time = args.get("start_datetime")  # ISO 8601 format
        end_time = args.get("end_datetime")  # ISO 8601 format

        data = {
            "schedules": attendee_emails,
            "startTime": {
                "dateTime": start_time,
                "timeZone": args.get("timezone", "Eastern Standard Time"),
            },
            "endTime": {
                "dateTime": end_time,
                "timeZone": args.get("timezone", "Eastern Standard Time"),
            },
            "availabilityViewInterval": args.get("interval_minutes", 30),
        }

        endpoint = "me/calendar/getSchedule"

        result = self._make_request("POST", endpoint, token, data)

        schedules = result.get("value", [])

        return {
            "start_time": start_time,
            "end_time": end_time,
            "attendees": [
                {
                    "email": schedule.get("scheduleId"),
                    "availability_view": schedule.get("availabilityView"),  # "0" = free, "2" = busy
                    "busy_times": schedule.get("scheduleItems", []),
                }
                for schedule in schedules
            ],
        }

    def update_event(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an existing calendar event"""
        token = self._get_access_token(org_id, user_id)

        event_id = args.get("event_id")

        # Build update payload
        update_data = {}

        if args.get("subject"):
            update_data["subject"] = args["subject"]
        if args.get("body"):
            update_data["body"] = {
                "contentType": "HTML" if args.get("is_html") else "Text",
                "content": args["body"],
            }
        if args.get("start_datetime"):
            update_data["start"] = {
                "dateTime": args["start_datetime"],
                "timeZone": args.get("timezone", "Eastern Standard Time"),
            }
        if args.get("end_datetime"):
            update_data["end"] = {
                "dateTime": args["end_datetime"],
                "timeZone": args.get("timezone", "Eastern Standard Time"),
            }
        if args.get("location"):
            update_data["location"] = {"displayName": args["location"]}
        if args.get("attendees"):
            update_data["attendees"] = [
                {"emailAddress": {"address": attendee}, "type": "required"}
                for attendee in args["attendees"]
            ]

        endpoint = f"me/events/{event_id}"

        result = self._make_request("PATCH", endpoint, token, update_data)

        return {
            "event_id": result.get("id"),
            "subject": result.get("subject"),
            "start_time": result["start"].get("dateTime"),
            "end_time": result["end"].get("dateTime"),
            "web_link": result.get("webLink"),
            "status": "updated",
        }

    def list_events(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List calendar events in a date range"""
        token = self._get_access_token(org_id, user_id)

        start_time = args.get("start_datetime")
        end_time = args.get("end_datetime")

        # Build query parameters
        params = []
        if start_time:
            params.append(f"startDateTime={start_time}")
        if end_time:
            params.append(f"endDateTime={end_time}")

        query_string = "&".join(params)
        endpoint = f"me/calendarview?{query_string}" if query_string else "me/events"

        result = self._make_request("GET", endpoint, token)

        events = result.get("value", [])

        return {
            "events": [
                {
                    "event_id": event.get("id"),
                    "subject": event.get("subject"),
                    "body": event.get("body", {}).get("content", ""),
                    "start_time": event["start"].get("dateTime"),
                    "end_time": event["end"].get("dateTime"),
                    "location": event.get("location", {}).get("displayName", ""),
                    "web_link": event.get("webLink"),
                    "organizer": event.get("organizer", {}).get("emailAddress", {}).get("address"),
                    "is_online_meeting": event.get("isOnlineMeeting", False),
                    "teams_link": event.get("onlineMeeting", {}).get("joinUrl"),
                    "attendees": [
                        {
                            "email": att["emailAddress"].get("address"),
                            "response_status": att.get("status", {}).get("response"),
                        }
                        for att in event.get("attendees", [])
                    ],
                }
                for event in events
            ],
            "count": len(events),
        }

    def cancel_event(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Cancel (delete) a calendar event"""
        token = self._get_access_token(org_id, user_id)

        event_id = args.get("event_id")
        comment = args.get("comment", "Event cancelled")

        # Cancel with notification
        endpoint = f"me/events/{event_id}/cancel"

        data = {"comment": comment}

        self._make_request("POST", endpoint, token, data)

        return {"event_id": event_id, "status": "cancelled"}
