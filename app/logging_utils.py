"""
Logging utilities for Stargate Lite connectors

Provides reusable decorators and sanitization helpers for consistent,
security-aware structured logging across all connectors.
"""

import functools
import time
from collections.abc import Callable
from types import TracebackType
from typing import Any, Literal, TypeVar

from app.logging_config import get_logger

F = TypeVar("F", bound=Callable[..., Any])

# Fields that should NEVER be logged - contains sensitive data
REDACTED_FIELDS: set[str] = {
    # Authentication tokens
    "access_token",
    "refresh_token",
    "bearer_token",
    "id_token",
    "authorization",
    # Secrets and keys
    "client_secret",
    "api_key",
    "secret_key",
    "private_key",
    "encryption_key",
    "password",
    "secret",
    # Financial PII
    "ssn",
    "social_security",
    "tax_id",
    "ein",
    "routing_number",
    "account_number",
    "card_number",
    "cvv",
    "pin",
    # OAuth
    "code",  # Authorization code
    "state",  # Contains org_id:user_id
}


def sanitize_args(args: dict[str, Any], max_depth: int = 2) -> dict[str, Any]:
    """
    Remove sensitive fields from args before logging.

    Args:
        args: Dictionary of arguments to sanitize
        max_depth: Maximum recursion depth for nested dicts

    Returns:
        Sanitized copy of args with sensitive values replaced by [REDACTED]
    """
    if not args or not isinstance(args, dict):
        return {}

    def should_redact(key: str) -> bool:
        """Check if a key should be redacted"""
        key_lower = key.lower()
        return any(field in key_lower for field in REDACTED_FIELDS)

    def sanitize_value(key: str, value: Any, depth: int) -> Any:
        """Recursively sanitize a value"""
        if should_redact(key):
            return "[REDACTED]"

        if isinstance(value, dict) and depth < max_depth:
            return {k: sanitize_value(k, v, depth + 1) for k, v in value.items()}

        if isinstance(value, list) and depth < max_depth:
            return [sanitize_value(key, item, depth + 1) for item in value[:5]]  # Limit list size

        # Truncate long strings
        if isinstance(value, str) and len(value) > 200:
            return value[:200] + "...[truncated]"

        return value

    return {k: sanitize_value(k, v, 0) for k, v in args.items()}


def log_operation(service: str, operation: str) -> Callable[[F], F]:
    """
    Decorator for connector methods - logs entry, exit, duration, and errors.

    Automatically captures:
    - Operation start with org_id, user_id
    - Operation success with duration_ms
    - Operation failure with error details

    Args:
        service: Service name (e.g., "quickbooks", "stripe")
        operation: Operation name (e.g., "create_vendor", "send_payment")

    Example:
        @log_operation("quickbooks", "create_vendor")
        def create_vendor(self, org_id, user_id, args):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(
            self: Any, org_id: str, user_id: str, args: dict[str, Any], *a: Any, **kw: Any
        ) -> Any:
            logger = get_logger(func.__module__)
            start = time.time()

            # Log operation start
            logger.info(
                f"{operation} started",
                service=service,
                operation=operation,
                org_id=org_id,
                user_id=user_id,
                log_event=f"{operation}_start",
            )

            try:
                result = func(self, org_id, user_id, args, *a, **kw)
                duration_ms = (time.time() - start) * 1000

                # Log operation success
                logger.info(
                    f"{operation} completed",
                    service=service,
                    operation=operation,
                    duration_ms=round(duration_ms, 2),
                    log_event=f"{operation}_success",
                )
                return result

            except Exception as e:
                duration_ms = (time.time() - start) * 1000

                # Log operation failure
                logger.error(
                    f"{operation} failed",
                    service=service,
                    operation=operation,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    error_message=str(e)[:200],  # Truncate to avoid logging secrets
                    log_event=f"{operation}_error",
                    exc_info=True,
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def log_token_refresh(service: str) -> Callable[[F], F]:
    """
    Decorator for token refresh methods - logs refresh attempts securely.

    Logs:
    - Refresh initiation
    - Success with new expiry (NEVER logs tokens)
    - Failure with error type

    Args:
        service: Service name (e.g., "quickbooks", "hubspot")

    Example:
        @log_token_refresh("quickbooks")
        def _refresh_token(self, org_id, user_id, refresh_token):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: Any, org_id: str, user_id: str, *args: Any, **kwargs: Any) -> Any:
            logger = get_logger(func.__module__)
            start = time.time()

            logger.info(
                "Token refresh initiated",
                service=service,
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_start",
            )

            try:
                result = func(self, org_id, user_id, *args, **kwargs)
                duration_ms = (time.time() - start) * 1000

                # Extract new expiry if available (safely)
                new_expiry = None
                if isinstance(result, dict):
                    expiry = result.get("token_expiry")
                    if expiry:
                        new_expiry = str(expiry)

                logger.info(
                    "Token refresh successful",
                    service=service,
                    org_id=org_id,
                    user_id=user_id,
                    duration_ms=round(duration_ms, 2),
                    new_expiry=new_expiry,
                    log_event="token_refresh_success",
                )
                return result

            except Exception as e:
                duration_ms = (time.time() - start) * 1000

                logger.error(
                    "Token refresh failed",
                    service=service,
                    org_id=org_id,
                    user_id=user_id,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    log_event="token_refresh_error",
                    exc_info=True,
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def log_credential_access(service: str, action: str = "retrieve") -> type[Any]:
    """
    Helper to log credential access events for audit trail.

    Args:
        service: Service name
        action: Action being performed (retrieve, store, delete)

    Returns:
        Context manager that logs credential access
    """
    logger = get_logger(__name__)

    class CredentialAccessLogger:
        def __init__(self, org_id: str, user_id: str, credential_type: str = "customer") -> None:
            self.org_id = org_id
            self.user_id = user_id
            self.credential_type = credential_type
            self.start_time: float = 0.0

        def __enter__(self) -> "CredentialAccessLogger":
            self.start_time = time.time()
            logger.debug(
                f"Credential {action} started",
                service=service,
                org_id=self.org_id,
                user_id=self.user_id,
                credential_type=self.credential_type,
                action=action,
                log_event=f"credential_{action}_start",
            )
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ) -> Literal[False]:
            duration_ms = (time.time() - self.start_time) * 1000

            if exc_type is None:
                logger.debug(
                    f"Credential {action} completed",
                    service=service,
                    org_id=self.org_id,
                    user_id=self.user_id,
                    duration_ms=round(duration_ms, 2),
                    log_event=f"credential_{action}_success",
                )
            else:
                logger.warning(
                    f"Credential {action} failed",
                    service=service,
                    org_id=self.org_id,
                    user_id=self.user_id,
                    duration_ms=round(duration_ms, 2),
                    error_type=exc_type.__name__,
                    log_event=f"credential_{action}_error",
                )
            return False  # Don't suppress exceptions

    return CredentialAccessLogger


def log_external_call(service: str, endpoint: str) -> Callable[[F], F]:
    """
    Decorator for external API calls - logs timing and status.

    Use this for OAuth token exchanges and other external HTTP calls
    that don't go through http_client.py.

    Args:
        service: Service name (e.g., "quickbooks", "google")
        endpoint: Endpoint description (e.g., "token_exchange", "userinfo")
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(func.__module__)
            start = time.time()

            logger.info(
                f"External call to {service}",
                service=service,
                endpoint=endpoint,
                log_event="external_call_start",
            )

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000

                # Try to get status code if result is a response object
                status_code = getattr(result, "status_code", None)

                logger.info(
                    "External call completed",
                    service=service,
                    endpoint=endpoint,
                    duration_ms=round(duration_ms, 2),
                    status_code=status_code,
                    log_event="external_call_success",
                )
                return result

            except Exception as e:
                duration_ms = (time.time() - start) * 1000

                logger.error(
                    "External call failed",
                    service=service,
                    endpoint=endpoint,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    log_event="external_call_error",
                    exc_info=True,
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator
