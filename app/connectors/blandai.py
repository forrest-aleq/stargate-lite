"""
Bland.ai connector for Stargate Lite
Handles AI phone calls and voice automation
Uses Bland.ai API (October 2025)
"""

import os
from typing import Any

from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class BlandAIConnector:
    """Bland.ai API connector for AI phone calling"""

    BASE_URL = "https://api.bland.ai/v1"

    def __init__(self) -> None:
        self.api_key = os.getenv("BLANDAI_API_KEY")

    def _get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _make_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()

        if method not in ["GET", "POST"]:
            raise ValueError(f"Unsupported method: {method}")

        if method == "GET":
            return http_client.get(url=url, service="blandai", headers=headers, params=data)
        else:
            # POST
            return http_client.post(url=url, service="blandai", headers=headers, json=data)

    def send_call(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send an AI phone call"""
        metadata = dict(args.get("metadata", {}))
        metadata.setdefault("org_id", org_id)
        metadata.setdefault("user_id", user_id)

        call_data = {
            "phone_number": args.get("phone_number"),
            "task": args.get("task"),  # AI prompt/instructions
            "voice": args.get("voice", "maya"),  # Voice ID
            "first_sentence": args.get("first_sentence", "Hello!"),
            "wait_for_greeting": args.get("wait_for_greeting", True),
            "record": args.get("record", True),
            "model": args.get("model", "enhanced"),  # base or enhanced
            "language": args.get("language", "en"),
            # Echo tenant identity in webhook payload for deterministic routing.
            "metadata": metadata,
        }

        # Optional webhook for call events
        if args.get("webhook"):
            call_data["webhook"] = args["webhook"]

        # Optional transfer settings
        if args.get("transfer_phone_number"):
            call_data["transfer_phone_number"] = args["transfer_phone_number"]

        # Optional max call duration
        if args.get("max_duration"):
            call_data["max_duration"] = args["max_duration"]

        result = self._make_request("POST", "/calls", call_data)

        return {
            "call_id": result.get("call_id"),
            "status": result.get("status"),
            "batch_id": result.get("batch_id"),
            "phone_number": args.get("phone_number"),
        }

    def send_batch_calls(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send multiple AI phone calls in batch"""
        metadata = dict(args.get("metadata", {}))
        metadata.setdefault("org_id", org_id)
        metadata.setdefault("user_id", user_id)

        batch_data = {
            "base_prompt": args.get("task"),
            "call_data": args.get("calls", []),  # List of {phone_number, task} dicts
            "voice": args.get("voice", "maya"),
            "model": args.get("model", "enhanced"),
            "metadata": metadata,
        }

        result = self._make_request("POST", "/batches", batch_data)

        return {
            "batch_id": result.get("batch_id"),
            "total_calls": len(args.get("calls", [])),
            "status": result.get("status"),
        }

    def get_call_status(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get status of a specific call"""
        call_id = args.get("call_id")

        result = self._make_request("GET", f"/calls/{call_id}")

        return {
            "call_id": result.get("call_id"),
            "status": result.get("status"),
            "duration": result.get("duration"),
            "recording_url": result.get("recording_url"),
            "transcript": result.get("transcript"),
            "answered_by": result.get("answered_by"),  # human or voicemail
            "completed_at": result.get("completed_at"),
        }

    def get_call_transcript(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get full transcript of a call"""
        call_id = args.get("call_id")

        result = self._make_request("GET", f"/calls/{call_id}/transcript")

        return {
            "call_id": call_id,
            "transcript": result.get("transcript"),
            "turns": result.get("turns", []),  # Detailed turn-by-turn conversation
            "summary": result.get("summary"),
        }

    def get_call_recording(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get recording URL for a call"""
        call_id = args.get("call_id")

        result = self._make_request("GET", f"/calls/{call_id}/recording")

        return {
            "call_id": call_id,
            "recording_url": result.get("recording_url"),
            "duration": result.get("duration"),
        }

    def list_calls(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List recent calls"""
        params = {"limit": args.get("limit", 50), "offset": args.get("offset", 0)}

        if args.get("status"):
            params["status"] = args["status"]  # completed, in-progress, failed

        result = self._make_request("GET", "/calls", params)

        return {
            "calls": [
                {
                    "call_id": c["call_id"],
                    "phone_number": c.get("phone_number"),
                    "status": c["status"],
                    "duration": c.get("duration"),
                    "created_at": c.get("created_at"),
                }
                for c in result.get("calls", [])
            ],
            "total": result.get("total"),
        }

    def create_phone_number(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Rent a phone number for outbound calls"""
        number_data = {"area_code": args.get("area_code"), "country": args.get("country", "US")}

        result = self._make_request("POST", "/phone-numbers", number_data)

        return {
            "phone_number": result.get("phone_number"),
            "phone_number_id": result.get("id"),
            "monthly_cost": result.get("monthly_cost", 15),  # $15/mo standard
        }
