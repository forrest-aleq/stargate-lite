"""
DocuSign connector for Stargate Lite
Handles envelopes, recipients, documents, and templates via eSignature REST API
"""

import base64
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from app.database import CredentialManager
from app.errors import CredentialMissingError
from app.http_client import http_client
from app.logging_config import get_logger
from app.posthog_client import track_token_refreshed

logger = get_logger(__name__)


class DocuSignConnector:
    """DocuSign eSignature API connector"""

    AUTH_URL = "https://account.docusign.com/oauth/token"
    DEMO_AUTH_URL = "https://account-d.docusign.com/oauth/token"

    def __init__(self) -> None:
        self.client_id = os.getenv("DOCUSIGN_CLIENT_ID")
        self.client_secret = os.getenv("DOCUSIGN_CLIENT_SECRET")
        self.environment = os.getenv("DOCUSIGN_ENVIRONMENT", "demo")

    def _get_base_url(self, account_id: str) -> str:
        """Get base URL for account"""
        if self.environment == "demo":
            return f"https://demo.docusign.net/restapi/v2.1/accounts/{account_id}"
        return f"https://na4.docusign.net/restapi/v2.1/accounts/{account_id}"

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token, refreshing if necessary"""
        cred = CredentialManager.get_credential(org_id, user_id, "docusign")

        if not cred:
            raise CredentialMissingError("docusign", org_id, user_id)

        if cred["token_expiry"] and cred["token_expiry"] < datetime.now(UTC) + timedelta(minutes=5):
            logger.info("Token expired, refreshing", service="docusign", org_id=org_id)
            return self._refresh_token(org_id, user_id, cred["refresh_token"])

        return cred

    def _refresh_token(self, org_id: str, user_id: str, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token"""
        auth_url = self.DEMO_AUTH_URL if self.environment == "demo" else self.AUTH_URL

        # DocuSign uses Basic auth for token refresh
        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        try:
            token_data = http_client.post(
                url=auth_url,
                service="docusign",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )

            new_expiry = datetime.now(UTC) + timedelta(seconds=token_data.get("expires_in", 28800))

            CredentialManager.store_credential(
                org_id=org_id,
                user_id=user_id,
                service="docusign",
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expiry=new_expiry,
            )

            # Track successful token refresh to PostHog
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="docusign",
                success=True,
            )

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_expiry": new_expiry,
                "account_id": token_data.get("account_id"),
            }
        except Exception:
            # Track failed token refresh to PostHog
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="docusign",
                success=False,
            )
            raise

    # ============ ENVELOPES ============

    def list_envelopes(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List envelopes from DocuSign"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)

        params = {}
        if args.get("from_date"):
            params["from_date"] = args["from_date"]
        if args.get("to_date"):
            params["to_date"] = args["to_date"]
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("folder_ids"):
            params["folder_ids"] = args["folder_ids"]
        if args.get("count"):
            params["count"] = min(args["count"], 100)

        url = f"{base_url}/envelopes"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
        )

        envelopes = result.get("envelopes", [])
        return {
            "envelopes": [
                {
                    "envelope_id": e["envelopeId"],
                    "status": e.get("status"),
                    "subject": e.get("emailSubject"),
                    "sent_date": e.get("sentDateTime"),
                    "completed_date": e.get("completedDateTime"),
                }
                for e in envelopes
            ],
            "result_set_size": result.get("resultSetSize", len(envelopes)),
            "total_set_size": result.get("totalSetSize", len(envelopes)),
        }

    def get_envelope(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get envelope details"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]

        result = http_client.get(
            url=f"{base_url}/envelopes/{envelope_id}",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "envelope_id": result["envelopeId"],
            "status": result.get("status"),
            "email_subject": result.get("emailSubject"),
            "email_blurb": result.get("emailBlurb"),
            "sender": result.get("sender"),
            "recipients": result.get("recipients"),
            "documents": result.get("envelopeDocuments", []),
            "created_date_time": result.get("createdDateTime"),
            "sent_date_time": result.get("sentDateTime"),
            "completed_date_time": result.get("completedDateTime"),
        }

    def create_envelope(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create and optionally send an envelope"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)

        envelope_data = {
            "emailSubject": args["email_subject"],
            "documents": args["documents"],
            "recipients": args["recipients"],
            "status": args.get("status", "created"),  # "sent" to send immediately
        }
        if args.get("email_blurb"):
            envelope_data["emailBlurb"] = args["email_blurb"]

        result = http_client.post(
            url=f"{base_url}/envelopes",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
            json=envelope_data,
        )

        return {
            "envelope_id": result["envelopeId"],
            "status": result.get("status"),
            "uri": result.get("uri"),
        }

    def send_envelope(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send a draft envelope"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]

        result = http_client.put(
            url=f"{base_url}/envelopes/{envelope_id}",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
            json={"status": "sent"},
        )

        return {
            "envelope_id": envelope_id,
            "status": result.get("status", "sent"),
        }

    def void_envelope(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Void an envelope"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]

        result = http_client.put(
            url=f"{base_url}/envelopes/{envelope_id}",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
            json={
                "status": "voided",
                "voidedReason": args["voided_reason"],
            },
        )

        return {
            "envelope_id": envelope_id,
            "status": result.get("status", "voided"),
        }

    # ============ RECIPIENTS ============

    def list_recipients(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List recipients for an envelope"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]

        result = http_client.get(
            url=f"{base_url}/envelopes/{envelope_id}/recipients",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "signers": result.get("signers", []),
            "carbon_copies": result.get("carbonCopies", []),
            "recipient_count": result.get("recipientCount", 0),
        }

    def update_recipient(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update recipient information"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]

        recipient_data = {
            "signers": [
                {
                    "recipientId": args["recipient_id"],
                    "name": args.get("name"),
                    "email": args.get("email"),
                }
            ]
        }

        http_client.put(
            url=f"{base_url}/envelopes/{envelope_id}/recipients",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
            json=recipient_data,
        )

        return {
            "recipient_id": args["recipient_id"],
            "status": "updated",
        }

    # ============ DOCUMENTS ============

    def list_documents(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List documents in an envelope"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]

        result = http_client.get(
            url=f"{base_url}/envelopes/{envelope_id}/documents",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
        )

        documents = result.get("envelopeDocuments", [])
        return {
            "documents": [
                {
                    "document_id": d["documentId"],
                    "name": d.get("name"),
                    "type": d.get("type"),
                    "uri": d.get("uri"),
                }
                for d in documents
            ],
        }

    def download_document(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Download a document from an envelope"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]
        document_id = args["document_id"]  # or "combined" for all docs

        # Get raw bytes
        result = http_client.get(
            url=f"{base_url}/envelopes/{envelope_id}/documents/{document_id}",
            service="docusign",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/pdf",
            },
            raw_response=True,
        )

        return {
            "document_base64": base64.b64encode(result).decode()
            if isinstance(result, bytes)
            else result,
            "content_type": "application/pdf",
        }

    # ============ TEMPLATES ============

    def list_templates(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List templates from DocuSign"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)

        params = {}
        if args.get("folder_id"):
            params["folder_id"] = args["folder_id"]
        if args.get("search_text"):
            params["search_text"] = args["search_text"]
        if args.get("count"):
            params["count"] = args["count"]

        url = f"{base_url}/templates"
        if params:
            url += "?" + urlencode(params)

        result = http_client.get(
            url=url,
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
        )

        templates = result.get("envelopeTemplates", [])
        return {
            "templates": [
                {
                    "template_id": t["templateId"],
                    "name": t.get("name"),
                    "description": t.get("description"),
                    "created": t.get("created"),
                }
                for t in templates
            ],
            "result_set_size": result.get("resultSetSize", len(templates)),
        }

    def create_envelope_from_template(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create envelope from a template"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)

        envelope_data = {
            "templateId": args["template_id"],
            "templateRoles": args["template_roles"],
            "status": args.get("status", "created"),
        }
        if args.get("email_subject"):
            envelope_data["emailSubject"] = args["email_subject"]

        result = http_client.post(
            url=f"{base_url}/envelopes",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
            json=envelope_data,
        )

        return {
            "envelope_id": result["envelopeId"],
            "status": result.get("status"),
        }

    def get_envelope_audit(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get audit events for an envelope"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]

        result = http_client.get(
            url=f"{base_url}/envelopes/{envelope_id}/audit_events",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "envelope_id": envelope_id,
            "audit_events": result.get("auditEvents", []),
        }

    def get_signing_url(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get an embedded signing URL for a recipient"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]

        recipient_view_data = {
            "recipientName": args["recipient_name"],
            "recipientEmail": args["recipient_email"],
            "returnUrl": args["return_url"],
            "authenticationMethod": "none",
        }

        result = http_client.post(
            url=f"{base_url}/envelopes/{envelope_id}/views/recipient",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
            json=recipient_view_data,
        )

        return {
            "envelope_id": envelope_id,
            "signing_url": result.get("url"),
        }

    def get_envelope_status(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get envelope status details"""
        cred = self._get_access_token(org_id, user_id)
        account_id = cred.get("account_id") or args.get("account_id")
        base_url = self._get_base_url(account_id)
        envelope_id = args["envelope_id"]

        result = http_client.get(
            url=f"{base_url}/envelopes/{envelope_id}",
            service="docusign",
            headers=self._get_headers(cred["access_token"]),
        )

        return {
            "envelope_id": result["envelopeId"],
            "status": result.get("status"),
            "status_changed_date_time": result.get("statusChangedDateTime"),
            "sent_date_time": result.get("sentDateTime"),
            "delivered_date_time": result.get("deliveredDateTime"),
            "completed_date_time": result.get("completedDateTime"),
            "voided_date_time": result.get("voidedDateTime"),
            "voided_reason": result.get("voidedReason"),
            "sender": result.get("sender"),
            "recipients_uri": result.get("recipientsUri"),
        }


# Singleton instance
docusign_connector = DocuSignConnector()
