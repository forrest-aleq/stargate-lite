"""
Communication Capability Registry
Gmail, Slack, Bland.AI, Twilio
"""

from app.registry.communication.gmail import GMAIL_CAPABILITIES
from app.registry.communication.slack import SLACK_CAPABILITIES
from app.registry.communication.voice import VOICE_CAPABILITIES

COMMUNICATION_CAPABILITIES = {
    **GMAIL_CAPABILITIES,
    **SLACK_CAPABILITIES,
    **VOICE_CAPABILITIES,
}
