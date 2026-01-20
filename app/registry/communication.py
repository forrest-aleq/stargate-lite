"""
Communication Capability Registry
Gmail, Slack, Bland.AI, Twilio
"""

from app.connectors.blandai import BlandAIConnector
from app.connectors.gmail import GmailConnector
from app.connectors.slack import SlackConnector
from app.connectors.twilio_sms import TwilioSMSConnector

# Initialize connectors
gmail_connector = GmailConnector()
slack_connector = SlackConnector()
blandai_connector = BlandAIConnector()
twilio_connector = TwilioSMSConnector()

COMMUNICATION_CAPABILITIES = {
    # ========== GMAIL ==========
    "email.send": {
        "handler": gmail_connector.send_email,
        "tool_name": "gmail.send_email",
        "description": "Send an email via Gmail",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.read": {
        "handler": gmail_connector.read_emails,
        "tool_name": "gmail.read_emails",
        "description": "Read emails from Gmail",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.draft": {
        "handler": gmail_connector.create_draft,
        "tool_name": "gmail.create_draft",
        "description": "Create a draft email in Gmail",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.get_history": {
        "handler": gmail_connector.get_history,
        "tool_name": "gmail.get_history",
        "description": "Fetch Gmail history changes for incremental sync (push notifications)",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.get_message_full": {
        "handler": gmail_connector.get_message_full,
        "tool_name": "gmail.get_message_full",
        "description": "Get full email message with headers, body, and attachments",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.download_attachment": {
        "handler": gmail_connector.download_attachment,
        "tool_name": "gmail.download_attachment",
        "description": "Download email attachment to specified path",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.setup_watch": {
        "handler": gmail_connector.setup_watch,
        "tool_name": "gmail.setup_watch",
        "description": "Set up Gmail push notifications watch",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.mark_as_read": {
        "handler": gmail_connector.mark_as_read,
        "tool_name": "gmail.mark_as_read",
        "description": "Mark email message as read",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.trash": {
        "handler": gmail_connector.trash_message,
        "tool_name": "gmail.trash_message",
        "description": "Move email message to trash",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.untrash": {
        "handler": gmail_connector.untrash_message,
        "tool_name": "gmail.untrash_message",
        "description": "Restore email message from trash",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.star": {
        "handler": gmail_connector.star_message,
        "tool_name": "gmail.star_message",
        "description": "Star or unstar an email message",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.reply": {
        "handler": gmail_connector.reply_to_email,
        "tool_name": "gmail.reply_to_email",
        "description": "Reply to an email in the same thread",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.forward": {
        "handler": gmail_connector.forward_email,
        "tool_name": "gmail.forward_email",
        "description": "Forward an email to another recipient",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.label.list": {
        "handler": gmail_connector.list_labels,
        "tool_name": "gmail.list_labels",
        "description": "List all labels in the mailbox",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.label.create": {
        "handler": gmail_connector.create_label,
        "tool_name": "gmail.create_label",
        "description": "Create a new label",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.label.apply": {
        "handler": gmail_connector.apply_labels,
        "tool_name": "gmail.apply_labels",
        "description": "Apply or remove labels from a message",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.thread.get": {
        "handler": gmail_connector.get_thread,
        "tool_name": "gmail.get_thread",
        "description": "Get a full email thread with all messages",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    "email.thread.list": {
        "handler": gmail_connector.list_threads,
        "tool_name": "gmail.list_threads",
        "description": "List email threads",
        "requires_oauth": True,
        "service": "google",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": (
            "Create aleq@yourcompany.com email account or grant delegate access"
        ),
    },
    # ========== SLACK ==========
    "message.send": {
        "handler": slack_connector.send_message,
        "tool_name": "slack.send_message",
        "description": "Send a message to a Slack channel",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "message.direct": {
        "handler": slack_connector.send_direct_message,
        "tool_name": "slack.send_direct_message",
        "description": "Send a direct message on Slack",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "file.upload": {
        "handler": slack_connector.upload_file,
        "tool_name": "slack.upload_file",
        "description": "Upload a file to Slack",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "channel.create": {
        "handler": slack_connector.create_channel,
        "tool_name": "slack.create_channel",
        "description": "Create a Slack channel",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "channel.invite": {
        "handler": slack_connector.invite_to_channel,
        "tool_name": "slack.invite_to_channel",
        "description": "Invite users to a Slack channel",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "channel.history": {
        "handler": slack_connector.get_channel_history,
        "tool_name": "slack.get_channel_history",
        "description": "Get message history from a Slack channel",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "channel.list": {
        "handler": slack_connector.list_channels,
        "tool_name": "slack.list_channels",
        "description": "List all channels in the workspace",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "channel.archive": {
        "handler": slack_connector.archive_channel,
        "tool_name": "slack.archive_channel",
        "description": "Archive a Slack channel",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "channel.topic": {
        "handler": slack_connector.set_channel_topic,
        "tool_name": "slack.set_channel_topic",
        "description": "Set the topic for a Slack channel",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "reaction.add": {
        "handler": slack_connector.add_reaction,
        "tool_name": "slack.add_reaction",
        "description": "Add a reaction to a message",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "reaction.remove": {
        "handler": slack_connector.remove_reaction,
        "tool_name": "slack.remove_reaction",
        "description": "Remove a reaction from a message",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "user.list": {
        "handler": slack_connector.list_users,
        "tool_name": "slack.list_users",
        "description": "List all users in the workspace",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "user.info": {
        "handler": slack_connector.get_user_info,
        "tool_name": "slack.get_user_info",
        "description": "Get detailed information about a user",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    "search.messages": {
        "handler": slack_connector.search_messages,
        "tool_name": "slack.search_messages",
        "description": "Search for messages in the workspace",
        "requires_oauth": True,
        "service": "slack",
        "credential_type": "agent",
        "supports_delegation": True,
        "delegation_instructions": "Add Aleq bot to your Slack workspace",
    },
    # ========== BLAND.AI ==========
    "voice.call.send": {
        "handler": blandai_connector.send_call,
        "tool_name": "blandai.send_call",
        "description": "Send AI phone call",
        "requires_oauth": False,
        "service": "blandai",
        "credential_type": None,
        "supports_delegation": False,
    },
    "voice.call.get": {
        "handler": blandai_connector.get_call_status,
        "tool_name": "blandai.get_call_status",
        "description": "Get call status details",
        "requires_oauth": False,
        "service": "blandai",
        "credential_type": None,
        "supports_delegation": False,
    },
    "voice.call.list": {
        "handler": blandai_connector.list_calls,
        "tool_name": "blandai.list_calls",
        "description": "List all calls",
        "requires_oauth": False,
        "service": "blandai",
        "credential_type": None,
        "supports_delegation": False,
    },
    "voice.batch.create": {
        "handler": blandai_connector.send_batch_calls,
        "tool_name": "blandai.send_batch_calls",
        "description": "Create batch calls",
        "requires_oauth": False,
        "service": "blandai",
        "credential_type": None,
        "supports_delegation": False,
    },
    "voice.transcript.get": {
        "handler": blandai_connector.get_call_transcript,
        "tool_name": "blandai.get_call_transcript",
        "description": "Get call transcript",
        "requires_oauth": False,
        "service": "blandai",
        "credential_type": None,
        "supports_delegation": False,
    },
    "voice.recording.get": {
        "handler": blandai_connector.get_call_recording,
        "tool_name": "blandai.get_call_recording",
        "description": "Get call recording URL",
        "requires_oauth": False,
        "service": "blandai",
        "credential_type": None,
        "supports_delegation": False,
    },
    "voice.phone.rent": {
        "handler": blandai_connector.create_phone_number,
        "tool_name": "blandai.create_phone_number",
        "description": "Rent phone number",
        "requires_oauth": False,
        "service": "blandai",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== TWILIO ==========
    "sms.send": {
        "handler": twilio_connector.send_sms,
        "tool_name": "twilio.send_sms",
        "description": "Send SMS message",
        "requires_oauth": False,
        "service": "twilio",
        "credential_type": None,
        "supports_delegation": False,
    },
    "mms.send": {
        "handler": twilio_connector.send_mms,
        "tool_name": "twilio.send_mms",
        "description": "Send MMS with media",
        "requires_oauth": False,
        "service": "twilio",
        "credential_type": None,
        "supports_delegation": False,
    },
    "sms.list": {
        "handler": twilio_connector.list_messages,
        "tool_name": "twilio.list_messages",
        "description": "List messages",
        "requires_oauth": False,
        "service": "twilio",
        "credential_type": None,
        "supports_delegation": False,
    },
    "sms.get": {
        "handler": twilio_connector.get_message,
        "tool_name": "twilio.get_message",
        "description": "Get message details",
        "requires_oauth": False,
        "service": "twilio",
        "credential_type": None,
        "supports_delegation": False,
    },
    "sms.schedule": {
        "handler": twilio_connector.schedule_message,
        "tool_name": "twilio.schedule_message",
        "description": "Schedule SMS for future send",
        "requires_oauth": False,
        "service": "twilio",
        "credential_type": None,
        "supports_delegation": False,
    },
    "sms.delete": {
        "handler": twilio_connector.delete_message,
        "tool_name": "twilio.delete_message",
        "description": "Delete message",
        "requires_oauth": False,
        "service": "twilio",
        "credential_type": None,
        "supports_delegation": False,
    },
}
