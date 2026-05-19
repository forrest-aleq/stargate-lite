"""Credential query helpers extracted from app.database."""

from typing import Any

from app.logging_config import get_logger

logger = get_logger(__name__)


def get_services_for_org(
    session_factory: Any,
    credential_model: Any,
    org_id: str,
    user_id: str,
    credential_type: str = "customer",
) -> list[str]:
    """Return distinct services with active credentials for org/user."""
    db = session_factory()
    try:
        credentials = (
            db.query(credential_model.service)
            .filter(
                credential_model.org_id == org_id,
                credential_model.user_id == user_id,
                credential_model.credential_type == credential_type,
            )
            .distinct()
            .all()
        )
        services = [cred.service for cred in credentials]
        logger.debug(
            "Retrieved services for org",
            org_id=org_id,
            user_id=user_id,
            services=services,
            log_event="get_services_for_org",
        )
        return services
    finally:
        db.close()


def resolve_credential_owner(
    session_factory: Any,
    credential_model: Any,
    service: str,
    *,
    realm_id: str | None = None,
    extra_data_matches: dict[str, str] | None = None,
    credential_type: str | None = None,
) -> dict[str, str] | None:
    """Resolve internal org/user identity from provider credential metadata."""
    realm_id_value = (realm_id or "").strip()
    extra_matches = {
        key.strip(): value.strip()
        for key, value in (extra_data_matches or {}).items()
        if isinstance(key, str) and isinstance(value, str) and key.strip() and value.strip()
    }

    if not realm_id_value and not extra_matches:
        return None

    db = session_factory()
    try:
        query = db.query(credential_model).filter(credential_model.service == service)
        if credential_type:
            query = query.filter(credential_model.credential_type == credential_type)

        candidates = query.order_by(credential_model.updated_at.desc()).all()

        for candidate in candidates:
            if realm_id_value and candidate.realm_id != realm_id_value:
                continue

            if extra_matches:
                candidate_extra = (
                    candidate.extra_data if isinstance(candidate.extra_data, dict) else {}
                )
                has_all_matches = all(
                    str(candidate_extra.get(key, "")).strip() == expected
                    for key, expected in extra_matches.items()
                )
                if not has_all_matches:
                    continue

            org_id = candidate.org_id
            user_id = candidate.user_id
            resolved_credential_type = candidate.credential_type
            if (
                not isinstance(org_id, str)
                or not org_id
                or not isinstance(user_id, str)
                or not user_id
                or not isinstance(resolved_credential_type, str)
                or not resolved_credential_type
            ):
                continue

            logger.debug(
                "Resolved credential owner from provider metadata",
                service=service,
                realm_id=realm_id_value or None,
                extra_data_keys=sorted(extra_matches.keys()) if extra_matches else [],
                org_id=org_id,
                user_id=user_id,
                credential_type=resolved_credential_type,
                log_event="credential_owner_resolved",
            )
            return {
                "org_id": org_id,
                "user_id": user_id,
                "credential_type": resolved_credential_type,
            }

        return None
    finally:
        db.close()
