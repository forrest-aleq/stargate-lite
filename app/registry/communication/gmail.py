"""
Gmail Capability Registry
"""

from app.connectors.gmail import GmailConnector

gmail_connector = GmailConnector()

_DELEGATION = {
    "credential_type": "agent",
    "supports_delegation": True,
    "delegation_instructions": (
        "Create aleq@yourcompany.com email account or grant delegate access"
    ),
}

GMAIL_CAPABILITIES = {
    "email.send": {
        "handler": gmail_connector.send_email,
        "tool_name": "gmail.send_email",
        "description": "Send an email via Gmail",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.read": {
        "handler": gmail_connector.read_emails,
        "tool_name": "gmail.read_emails",
        "description": "Read emails from Gmail",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.draft": {
        "handler": gmail_connector.create_draft,
        "tool_name": "gmail.create_draft",
        "description": "Create a draft email in Gmail",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.get_history": {
        "handler": gmail_connector.get_history,
        "tool_name": "gmail.get_history",
        "description": "Fetch Gmail history changes for incremental sync (push notifications)",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.get_message_full": {
        "handler": gmail_connector.get_message_full,
        "tool_name": "gmail.get_message_full",
        "description": "Get full email message with headers, body, and attachments",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.download_attachment": {
        "handler": gmail_connector.download_attachment,
        "tool_name": "gmail.download_attachment",
        "description": "Download email attachment to specified path",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.setup_watch": {
        "handler": gmail_connector.setup_watch,
        "tool_name": "gmail.setup_watch",
        "description": "Set up Gmail push notifications watch",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.mark_as_read": {
        "handler": gmail_connector.mark_as_read,
        "tool_name": "gmail.mark_as_read",
        "description": "Mark email message as read",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.trash": {
        "handler": gmail_connector.trash_message,
        "tool_name": "gmail.trash_message",
        "description": "Move email message to trash",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.untrash": {
        "handler": gmail_connector.untrash_message,
        "tool_name": "gmail.untrash_message",
        "description": "Restore email message from trash",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.star": {
        "handler": gmail_connector.star_message,
        "tool_name": "gmail.star_message",
        "description": "Star or unstar an email message",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.reply": {
        "handler": gmail_connector.reply_to_email,
        "tool_name": "gmail.reply_to_email",
        "description": "Reply to an email in the same thread",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.forward": {
        "handler": gmail_connector.forward_email,
        "tool_name": "gmail.forward_email",
        "description": "Forward an email to another recipient",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.label.list": {
        "handler": gmail_connector.list_labels,
        "tool_name": "gmail.list_labels",
        "description": "List all labels in the mailbox",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.label.create": {
        "handler": gmail_connector.create_label,
        "tool_name": "gmail.create_label",
        "description": "Create a new label",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.label.apply": {
        "handler": gmail_connector.apply_labels,
        "tool_name": "gmail.apply_labels",
        "description": "Apply or remove labels from a message",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.thread.get": {
        "handler": gmail_connector.get_thread,
        "tool_name": "gmail.get_thread",
        "description": "Get a full email thread with all messages",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
    "email.thread.list": {
        "handler": gmail_connector.list_threads,
        "tool_name": "gmail.list_threads",
        "description": "List email threads",
        "requires_oauth": True,
        "service": "google",
        **_DELEGATION,
    },
}
