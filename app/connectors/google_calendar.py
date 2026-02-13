"""
Google Calendar connector for Stargate Lite
Handles calendar event management via Calendar API v3
Uses domain-wide delegation to impersonate user (Option B per architecture decision)
Shares OAuth credentials with Gmail/Drive/Sheets (service="google")
"""

import os
from datetime import UTC, datetime
from typing import Any, ClassVar

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)


class GoogleCalendarConnector:
    """Google Calendar API connector"""

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
        """Get valid Google credentials (shared with Gmail/Drive/Sheets), refreshing if necessary"""
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
                    service="google_calendar",
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
                        service="google_calendar",
                        org_id=org_id,
                        user_id=user_id,
                        log_event="token_refresh_success",
                    )
                except Exception as e:
                    logger.error(
                        "Google token refresh failed",
                        service="google_calendar",
                        org_id=org_id,
                        user_id=user_id,
                        error_type=type(e).__name__,
                        log_event="token_refresh_error",
                        exc_info=True,
                    )
                    raise

        return creds

    def create_event(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a calendar event (impersonating user per domain-wide delegation)"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("calendar", "v3", credentials=creds)

            # Build event structure
            event = {
                "summary": args.get("summary"),
                "description": args.get("description", ""),
                "start": {
                    "dateTime": args.get("start_datetime"),  # ISO 8601 format
                    "timeZone": args.get("timezone", "America/New_York"),
                },
                "end": {
                    "dateTime": args.get("end_datetime"),  # ISO 8601 format
                    "timeZone": args.get("timezone", "America/New_York"),
                },
            }

            # Add attendees if provided
            if args.get("attendees"):
                event["attendees"] = [{"email": attendee} for attendee in args["attendees"]]

            # Add location if provided
            if args.get("location"):
                event["location"] = args["location"]

            # Add reminders if provided
            if args.get("reminders"):
                event["reminders"] = {"useDefault": False, "overrides": args["reminders"]}

            # Add conferencing (Google Meet) if requested
            if args.get("add_conference"):
                event["conferenceData"] = {
                    "createRequest": {
                        "requestId": f"{org_id}_{user_id}_{datetime.now().timestamp()}"
                    }
                }

            # Create the event
            calendar_id = args.get("calendar_id", "primary")
            created_event = (
                service.events()
                .insert(
                    calendarId=calendar_id,
                    body=event,
                    conferenceDataVersion=1 if args.get("add_conference") else 0,
                    sendUpdates="all",  # Send email invitations to attendees
                )
                .execute()
            )

            return {
                "event_id": created_event.get("id"),
                "summary": created_event.get("summary"),
                "start_time": created_event["start"].get("dateTime"),
                "end_time": created_event["end"].get("dateTime"),
                "html_link": created_event.get("htmlLink"),
                "hangout_link": created_event.get("hangoutLink"),
                "status": created_event.get("status"),
                "attendees": [
                    {"email": att.get("email"), "response_status": att.get("responseStatus")}
                    for att in created_event.get("attendees", [])
                ],
            }

        except HttpError as error:
            raise Exception(f"Google Calendar API error: {error}") from error

    def check_availability(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Check free/busy time for attendees"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("calendar", "v3", credentials=creds)

            attendee_emails = args.get("attendees", [])
            time_min = args.get("time_min")  # ISO 8601 format
            time_max = args.get("time_max")  # ISO 8601 format

            body = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": email} for email in attendee_emails],
            }

            events_result = service.freebusy().query(body=body).execute()

            calendars = events_result.get("calendars", {})

            return {
                "time_min": time_min,
                "time_max": time_max,
                "attendees": [
                    {
                        "email": email,
                        "busy_times": calendars.get(email, {}).get("busy", []),
                        "errors": calendars.get(email, {}).get("errors", []),
                    }
                    for email in attendee_emails
                ],
            }

        except HttpError as error:
            raise Exception(f"Google Calendar API error: {error}") from error

    def update_event(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an existing calendar event"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("calendar", "v3", credentials=creds)

            event_id = args.get("event_id")
            calendar_id = args.get("calendar_id", "primary")

            # Get existing event
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

            # Update fields if provided
            if args.get("summary"):
                event["summary"] = args["summary"]
            if args.get("description"):
                event["description"] = args["description"]
            if args.get("start_datetime"):
                event["start"]["dateTime"] = args["start_datetime"]
            if args.get("end_datetime"):
                event["end"]["dateTime"] = args["end_datetime"]
            if args.get("location"):
                event["location"] = args["location"]
            if args.get("attendees"):
                event["attendees"] = [{"email": attendee} for attendee in args["attendees"]]

            # Update the event
            updated_event = (
                service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=event, sendUpdates="all")
                .execute()
            )

            return {
                "event_id": updated_event.get("id"),
                "summary": updated_event.get("summary"),
                "start_time": updated_event["start"].get("dateTime"),
                "end_time": updated_event["end"].get("dateTime"),
                "html_link": updated_event.get("htmlLink"),
                "status": "updated",
            }

        except HttpError as error:
            raise Exception(f"Google Calendar API error: {error}") from error

    def list_events(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List calendar events in a date range"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("calendar", "v3", credentials=creds)

            calendar_id = args.get("calendar_id", "primary")
            time_min = args.get("time_min", datetime.now(UTC).isoformat() + "Z")
            time_max = args.get("time_max")  # Optional
            max_results = args.get("max_results", 50)

            events_result = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])

            return {
                "events": [
                    {
                        "event_id": event.get("id"),
                        "summary": event.get("summary"),
                        "description": event.get("description", ""),
                        "start_time": event["start"].get("dateTime", event["start"].get("date")),
                        "end_time": event["end"].get("dateTime", event["end"].get("date")),
                        "location": event.get("location", ""),
                        "html_link": event.get("htmlLink"),
                        "organizer": event.get("organizer", {}).get("email"),
                        "attendees": [
                            {
                                "email": att.get("email"),
                                "response_status": att.get("responseStatus"),
                            }
                            for att in event.get("attendees", [])
                        ],
                    }
                    for event in events
                ],
                "count": len(events),
                "next_page_token": events_result.get("nextPageToken"),
            }

        except HttpError as error:
            raise Exception(f"Google Calendar API error: {error}") from error

    def cancel_event(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Cancel (delete) a calendar event"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("calendar", "v3", credentials=creds)

            event_id = args.get("event_id")
            calendar_id = args.get("calendar_id", "primary")

            # Delete the event
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates="all",  # Send cancellation emails
            ).execute()

            return {"event_id": event_id, "status": "cancelled"}

        except HttpError as error:
            raise Exception(f"Google Calendar API error: {error}") from error

    def get_event(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a single calendar event"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("calendar", "v3", credentials=creds)

            event_id = args.get("event_id")
            calendar_id = args.get("calendar_id", "primary")

            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

            return {
                "event_id": event.get("id"),
                "summary": event.get("summary"),
                "description": event.get("description", ""),
                "start": event.get("start"),
                "end": event.get("end"),
                "status": event.get("status"),
                "attendees": [
                    {
                        "email": att.get("email"),
                        "response_status": att.get("responseStatus"),
                    }
                    for att in event.get("attendees", [])
                ],
            }

        except HttpError as error:
            raise Exception(f"Google Calendar API error: {error}") from error

    def list_calendars(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List user's calendars"""
        creds = self._get_credentials(org_id, user_id)

        try:
            service = build("calendar", "v3", credentials=creds)

            calendar_list = service.calendarList().list().execute()

            calendars = calendar_list.get("items", [])

            return {
                "calendars": [
                    {
                        "calendar_id": cal.get("id"),
                        "summary": cal.get("summary"),
                        "primary": cal.get("primary", False),
                        "timezone": cal.get("timeZone"),
                    }
                    for cal in calendars
                ],
                "count": len(calendars),
            }

        except HttpError as error:
            raise Exception(f"Google Calendar API error: {error}") from error
