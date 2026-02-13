"""
Database module for Stargate Lite
Handles secure credential storage with encryption
"""

import os
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from sqlalchemy import JSON, Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stargate_lite.db")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Initialize Fernet cipher
if not ENCRYPTION_KEY:
    raise RuntimeError(
        "ENCRYPTION_KEY environment variable is required!\n"
        "Generate one with: python -c 'from cryptography.fernet import Fernet; "
        "print(Fernet.generate_key().decode())'\n"
        "Then add it to your .env file: ENCRYPTION_KEY=<generated_key>"
    )

_key = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
cipher = Fernet(_key)

# SQLAlchemy setup with production-ready connection pooling
if "sqlite" in DATABASE_URL:
    # SQLite: Simple config for development/testing
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL/MySQL: Production pooling configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,  # Supabase-friendly pool size
        max_overflow=5,  # Extra connections when pool exhausted
        pool_pre_ping=True,  # Test connections before use (detect stale connections)
        pool_recycle=300,  # Recycle connections every 5 min (Supabase timeouts)
        pool_timeout=30,  # Wait 30s for connection before raising error
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
_utcnow = lambda: datetime.now(UTC)  # noqa: E731


class CredentialStore(Base):
    """Table for storing encrypted OAuth credentials with dual credential system"""

    __tablename__ = "stargate_credentials"

    # Composite primary key: org_id:user_id:service:credential_type
    id = Column(String, primary_key=True)
    org_id = Column(String, nullable=False, index=True)
    # Can be "ALEQ_AGENT" for agent credentials
    user_id = Column(String, nullable=False, index=True)
    service = Column(String, nullable=False, index=True)

    # NEW: Credential type classification (agent or customer)
    credential_type = Column(String, nullable=False, index=True)  # "agent" or "customer"

    # NEW: Access pattern for agent credentials
    # "programmatic", "delegate", or null (for customer creds)
    access_pattern = Column(String, nullable=True)

    # Encrypted fields
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=True)

    # Metadata
    token_expiry = Column(DateTime, nullable=True)
    realm_id = Column(String, nullable=True)  # QuickBooks specific
    extra_data = Column(JSON, nullable=True)  # Store additional service-specific data
    created_by = Column(String, nullable=True)  # User who set up this credential

    # Audit fields
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


def init_db() -> None:
    """Initialize the database.

    When SKIP_ALEMBIC=true (Supabase), migrations are managed by Supabase CLI
    so we skip Alembic entirely.  For local SQLite dev, Alembic runs as before.
    """
    if os.getenv("SKIP_ALEMBIC", "").lower() == "true":
        logger.info(
            "Skipping Alembic migrations (SKIP_ALEMBIC=true)",
            database_type="postgresql",
            log_event="database_init",
        )
        return

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info(
        "Database migrations applied",
        database_type="sqlite" if "sqlite" in DATABASE_URL else "postgresql",
        log_event="database_init",
    )


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CredentialManager:
    """Manager for encrypted credential operations with dual credential system"""

    @staticmethod
    def _encrypt(value: str) -> str:
        """Encrypt a string value"""
        return cipher.encrypt(value.encode()).decode()

    @staticmethod
    def _decrypt(encrypted_value: str) -> str:
        """Decrypt a string value"""
        return cipher.decrypt(encrypted_value.encode()).decode()

    @staticmethod
    def _update_existing_credential(
        existing: CredentialStore,
        access_token: str,
        refresh_token: str | None,
        token_expiry: datetime | None,
        realm_id: str | None,
        access_pattern: str | None,
        extra_data: dict[str, Any] | None,
        service: str,
        org_id: str,
        user_id: str,
    ) -> None:
        """Update an existing credential record."""
        logger.debug(
            "Updating existing credential",
            service=service,
            org_id=org_id,
            user_id=user_id,
            log_event="credential_update",
        )
        existing.access_token_encrypted = CredentialManager._encrypt(access_token)
        if refresh_token:
            existing.refresh_token_encrypted = CredentialManager._encrypt(refresh_token)
        existing.token_expiry = token_expiry
        existing.realm_id = realm_id
        existing.access_pattern = access_pattern
        existing.extra_data = extra_data or {}
        existing.updated_at = datetime.now(UTC)

    @staticmethod
    def _create_new_credential(
        credential_id: str,
        org_id: str,
        user_id: str,
        service: str,
        credential_type: str,
        access_pattern: str | None,
        access_token: str,
        refresh_token: str | None,
        token_expiry: datetime | None,
        realm_id: str | None,
        extra_data: dict[str, Any] | None,
        created_by: str | None,
    ) -> CredentialStore:
        """Create a new credential record."""
        logger.debug(
            "Creating new credential",
            service=service,
            org_id=org_id,
            user_id=user_id,
            log_event="credential_create",
        )
        return CredentialStore(
            id=credential_id,
            org_id=org_id,
            user_id=user_id,
            service=service,
            credential_type=credential_type,
            access_pattern=access_pattern,
            access_token_encrypted=CredentialManager._encrypt(access_token),
            refresh_token_encrypted=(
                CredentialManager._encrypt(refresh_token) if refresh_token else None
            ),
            token_expiry=token_expiry,
            realm_id=realm_id,
            extra_data=extra_data or {},
            created_by=created_by,
        )

    @staticmethod
    def store_credential(
        org_id: str,
        user_id: str,
        service: str,
        access_token: str,
        refresh_token: str | None = None,
        token_expiry: datetime | None = None,
        realm_id: str | None = None,
        credential_type: str | None = None,
        access_pattern: str | None = None,
        extra_data: dict[str, Any] | None = None,
        created_by: str | None = None,
    ) -> None:
        """Store or update credentials with credential type classification."""
        credential_type = credential_type or "customer"
        credential_id = f"{org_id}:{user_id}:{service}:{credential_type}"

        logger.info(
            "Storing credential",
            service=service,
            org_id=org_id,
            user_id=user_id,
            credential_type=credential_type,
            log_event="credential_store_start",
        )

        db = SessionLocal()
        try:
            existing = db.query(CredentialStore).filter_by(id=credential_id).first()

            if existing:
                CredentialManager._update_existing_credential(
                    existing,
                    access_token,
                    refresh_token,
                    token_expiry,
                    realm_id,
                    access_pattern,
                    extra_data,
                    service,
                    org_id,
                    user_id,
                )
            else:
                new_cred = CredentialManager._create_new_credential(
                    credential_id,
                    org_id,
                    user_id,
                    service,
                    credential_type,
                    access_pattern,
                    access_token,
                    refresh_token,
                    token_expiry,
                    realm_id,
                    extra_data,
                    created_by,
                )
                db.add(new_cred)

            db.commit()
            logger.info(
                "Credential stored successfully",
                service=service,
                org_id=org_id,
                user_id=user_id,
                credential_type=credential_type,
                token_expiry=token_expiry.isoformat() if token_expiry else None,
                log_event="credential_store_success",
            )
        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to store credential",
                service=service,
                org_id=org_id,
                user_id=user_id,
                error_type=type(e).__name__,
                log_event="credential_store_error",
                exc_info=True,
            )
            raise e
        finally:
            db.close()

    @staticmethod
    def get_credential(
        org_id: str,
        user_id: str,
        service: str,
        credential_type: str | None = None,  # NEW: Optional for backward compatibility
    ) -> dict[str, Any] | None:
        """
        Retrieve and decrypt credentials for a specific credential type

        If credential_type is not provided, defaults to "customer" for backward compatibility.
        """
        # Default to customer for backward compatibility
        if credential_type is None:
            credential_type = "customer"

        logger.debug(
            "Retrieving credential",
            service=service,
            org_id=org_id,
            user_id=user_id,
            credential_type=credential_type,
            log_event="credential_get_start",
        )

        db = SessionLocal()
        try:
            credential_id = f"{org_id}:{user_id}:{service}:{credential_type}"
            cred = db.query(CredentialStore).filter_by(id=credential_id).first()

            if not cred:
                logger.warning(
                    "Credential not found",
                    service=service,
                    org_id=org_id,
                    user_id=user_id,
                    credential_type=credential_type,
                    log_event="credential_not_found",
                )
                return None

            is_expired = cred.token_expiry and cred.token_expiry < datetime.now(UTC)

            logger.debug(
                "Credential retrieved",
                service=service,
                org_id=org_id,
                user_id=user_id,
                credential_type=credential_type,
                expired=is_expired,
                token_expiry=(cred.token_expiry.isoformat() if cred.token_expiry else None),
                log_event="credential_get_success",
            )

            if cred.access_token_encrypted is None:
                logger.error(
                    "Credential found but access_token_encrypted is None",
                    service=service,
                    org_id=org_id,
                    user_id=user_id,
                    log_event="credential_data_corrupted",
                )
                return None
            return {
                "access_token": CredentialManager._decrypt(cred.access_token_encrypted),
                "refresh_token": (
                    CredentialManager._decrypt(cred.refresh_token_encrypted)
                    if cred.refresh_token_encrypted
                    else None
                ),
                "token_expiry": cred.token_expiry,
                "realm_id": cred.realm_id,
                "credential_type": cred.credential_type,
                "access_pattern": cred.access_pattern,
                "extra_data": cred.extra_data or {},
            }
        finally:
            db.close()

    @staticmethod
    def get_credential_for_capability(
        capability_key: str, org_id: str, user_id: str, use_delegation: bool = False
    ) -> dict[str, Any] | None:
        """
        Get credential for a capability, respecting credential_type hierarchy

        For agent credentials:
        1. Try delegated agent credential (if use_delegation=True and supported)
        2. Fall back to system agent credential (ALEQ_SYSTEM)

        For customer credentials:
        1. User's customer credential
        """
        # Import here to avoid circular dependency
        from app.registry import get_capability

        capability = get_capability(capability_key)
        if not capability:
            return None

        service = capability["service"]
        cred_type = capability.get("credential_type")

        # No credentials needed
        if not capability.get("requires_oauth") or cred_type is None:
            return None

        if cred_type == "agent":
            # Try delegation first if requested and supported
            if use_delegation and capability.get("supports_delegation"):
                cred = CredentialManager.get_credential(
                    org_id=org_id, user_id="ALEQ_AGENT", service=service, credential_type="agent"
                )
                if cred and cred.get("access_pattern") == "delegate":
                    return cred

            # Fall back to Aleq's system credential
            cred = CredentialManager.get_credential(
                org_id="ALEQ_SYSTEM", user_id="ALEQ_AGENT", service=service, credential_type="agent"
            )
            return cred

        elif cred_type == "customer":
            # Customer credentials - use provided org_id/user_id
            cred = CredentialManager.get_credential(
                org_id=org_id, user_id=user_id, service=service, credential_type="customer"
            )
            return cred

        return None

    @staticmethod
    def delete_credential(
        org_id: str,
        user_id: str,
        service: str,
        credential_type: str | None = None,  # NEW: Optional for backward compatibility
    ) -> bool:
        """
        Delete credentials for a user

        If credential_type is not provided, defaults to "customer" for backward compatibility.
        """
        # Default to customer for backward compatibility
        if credential_type is None:
            credential_type = "customer"

        logger.info(
            "Deleting credential",
            service=service,
            org_id=org_id,
            user_id=user_id,
            credential_type=credential_type,
            log_event="credential_delete_start",
        )

        db = SessionLocal()
        try:
            credential_id = f"{org_id}:{user_id}:{service}:{credential_type}"
            cred = db.query(CredentialStore).filter_by(id=credential_id).first()
            if cred:
                db.delete(cred)
                db.commit()
                logger.info(
                    "Credential deleted successfully",
                    service=service,
                    org_id=org_id,
                    user_id=user_id,
                    credential_type=credential_type,
                    log_event="credential_delete_success",
                )
                return True

            logger.warning(
                "Credential not found for deletion",
                service=service,
                org_id=org_id,
                user_id=user_id,
                credential_type=credential_type,
                log_event="credential_delete_not_found",
            )
            return False
        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to delete credential",
                service=service,
                org_id=org_id,
                user_id=user_id,
                error_type=type(e).__name__,
                log_event="credential_delete_error",
                exc_info=True,
            )
            raise e
        finally:
            db.close()

    @staticmethod
    def get_all_credentials() -> list[dict[str, Any]]:
        """Get all credential records for health monitoring"""
        db = SessionLocal()
        try:
            credentials = db.query(CredentialStore).all()
            return [
                {
                    "service": cred.service,
                    "org_id": cred.org_id,
                    "user_id": cred.user_id,
                    "credential_type": cred.credential_type,
                    "access_pattern": cred.access_pattern,
                    "token_expiry": cred.token_expiry,
                    "updated_at": cred.updated_at,
                }
                for cred in credentials
            ]
        finally:
            db.close()

    @staticmethod
    def get_services_for_org(
        org_id: str,
        user_id: str,
        credential_type: str = "customer",
    ) -> list[str]:
        """
        Return list of services with active credentials for org/user.

        Used by FCI utilities to discover which connectors are available
        for aggregation without needing to know in advance.
        """
        db = SessionLocal()
        try:
            credentials = (
                db.query(CredentialStore.service)
                .filter(
                    CredentialStore.org_id == org_id,
                    CredentialStore.user_id == user_id,
                    CredentialStore.credential_type == credential_type,
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
