"""
Helpers for resolving internal org/user identity from provider webhook payloads.
"""

import asyncio

from app.database import CredentialManager
from app.logging_config import get_logger

logger = get_logger(__name__)


async def resolve_webhook_identity(
    service: str,
    *,
    fallback_org_id: str,
    fallback_user_id: str | None = None,
    realm_id: str | None = None,
    extra_data_matches: dict[str, str] | None = None,
    credential_type: str | None = None,
) -> tuple[str, str | None]:
    """Resolve webhook org/user identity to internal IDs when possible.

    Falls back to the provided IDs if no credential-backed mapping is found.
    """
    try:
        resolved = await asyncio.to_thread(
            CredentialManager.resolve_credential_owner,
            service,
            realm_id=realm_id,
            extra_data_matches=extra_data_matches,
            credential_type=credential_type,
        )
    except Exception:
        logger.warning(
            "Credential owner resolution failed; using webhook fallback identity",
            service=service,
            fallback_org_id=fallback_org_id,
            log_event="webhook_identity_resolution_failed",
            exc_info=True,
        )
        return fallback_org_id, fallback_user_id

    if not resolved:
        return fallback_org_id, fallback_user_id

    return resolved["org_id"], resolved["user_id"]
