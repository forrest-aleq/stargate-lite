"""
Slack messaging mixin for message operations.
"""

from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .base import SlackBase


class MessagingMixin(SlackBase):
    """Mixin with message operations."""

    def send_message(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a message to a Slack channel or user"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel = args.get("channel")
            text = args.get("text")
            blocks = args.get("blocks")
            thread_ts = args.get("thread_ts")

            response = client.chat_postMessage(
                channel=channel, text=text, blocks=blocks, thread_ts=thread_ts
            )

            return {
                "message_id": response["ts"],
                "channel": response["channel"],
                "text": text,
                "status": "sent",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def send_direct_message(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a direct message to a Slack user"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            slack_user_id = args.get("user_id")
            text = args.get("text")

            dm_response = client.conversations_open(users=slack_user_id)
            channel_id = dm_response["channel"]["id"]

            response = client.chat_postMessage(channel=channel_id, text=text)

            return {
                "message_id": response["ts"],
                "channel": channel_id,
                "text": text,
                "status": "sent",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def update_message(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Update (edit) a message"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel = args.get("channel_id")
            ts = args.get("timestamp")
            text = args.get("text")

            response = client.chat_update(channel=channel, ts=ts, text=text)

            return {
                "channel": response["channel"],
                "timestamp": response["ts"],
                "text": text,
                "status": "updated",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def delete_message(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Delete a message"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel = args.get("channel_id")
            ts = args.get("timestamp")

            client.chat_delete(channel=channel, ts=ts)

            return {"channel": channel, "timestamp": ts, "status": "deleted"}

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def pin_message(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Pin a message to a channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel = args.get("channel_id")
            ts = args.get("timestamp")

            client.pins_add(channel=channel, timestamp=ts)

            return {"channel": channel, "timestamp": ts, "status": "pinned"}

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def unpin_message(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Unpin a message from a channel"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel = args.get("channel_id")
            ts = args.get("timestamp")

            client.pins_remove(channel=channel, timestamp=ts)

            return {"channel": channel, "timestamp": ts, "status": "unpinned"}

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def schedule_message(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Schedule a message for future delivery"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel = args.get("channel_id")
            text = args.get("text")
            post_at = args.get("post_at")

            response = client.chat_scheduleMessage(
                channel=channel, text=text, post_at=post_at
            )

            return {
                "scheduled_message_id": response["scheduled_message_id"],
                "channel": response["channel"],
                "post_at": response["post_at"],
                "status": "scheduled",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def get_thread_replies(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get replies in a message thread"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel = args.get("channel_id")
            ts = args.get("timestamp")
            limit = args.get("limit", 100)

            response = client.conversations_replies(
                channel=channel, ts=ts, limit=limit
            )

            messages = [
                {
                    "text": msg.get("text"),
                    "user": msg.get("user"),
                    "timestamp": msg.get("ts"),
                    "thread_ts": msg.get("thread_ts"),
                }
                for msg in response["messages"]
            ]

            return {
                "channel": channel,
                "thread_ts": ts,
                "messages": messages,
                "count": len(messages),
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def add_reaction(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Add a reaction to a message"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            timestamp = args.get("timestamp")
            name = args.get("name")

            client.reactions_add(
                channel=channel_id, timestamp=timestamp, name=name
            )

            return {
                "channel_id": channel_id,
                "timestamp": timestamp,
                "reaction": name,
                "status": "added",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def remove_reaction(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Remove a reaction from a message"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            channel_id = args.get("channel_id")
            timestamp = args.get("timestamp")
            name = args.get("name")

            client.reactions_remove(
                channel=channel_id, timestamp=timestamp, name=name
            )

            return {
                "channel_id": channel_id,
                "timestamp": timestamp,
                "reaction": name,
                "status": "removed",
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e

    def search_messages(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Search for messages in the workspace"""
        token = self._get_access_token(org_id, user_id)
        client = WebClient(token=token)

        try:
            query = args.get("query")
            count = args.get("count", 20)
            sort = args.get("sort", "timestamp")
            sort_dir = args.get("sort_dir", "desc")

            response = client.search_messages(
                query=query, count=count, sort=sort, sort_dir=sort_dir
            )

            messages_data = response.get("messages") or {}
            matches = messages_data.get("matches", [])
            messages = [
                {
                    "text": msg.get("text"),
                    "user": msg.get("user"),
                    "username": msg.get("username"),
                    "timestamp": msg.get("ts"),
                    "channel_id": msg.get("channel", {}).get("id"),
                    "channel_name": msg.get("channel", {}).get("name"),
                    "permalink": msg.get("permalink"),
                }
                for msg in matches
            ]

            return {
                "query": query,
                "messages": messages,
                "count": len(messages),
                "total": messages_data.get("total", 0),
            }

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}") from e
