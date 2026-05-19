"""
Voice/SMS Capability Registry (Bland.AI, Twilio)
"""

from app.connectors.blandai import BlandAIConnector
from app.connectors.twilio_sms import TwilioSMSConnector

blandai_connector = BlandAIConnector()
twilio_connector = TwilioSMSConnector()

VOICE_CAPABILITIES = {
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
    "sms.incoming.list": {
        "handler": twilio_connector.get_incoming_messages,
        "tool_name": "twilio.get_incoming_messages",
        "description": "List incoming SMS messages received by Aleq's number",
        "requires_oauth": False,
        "service": "twilio",
        "credential_type": None,
        "supports_delegation": False,
    },
}
