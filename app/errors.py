"""
Stargate Error Taxonomy
Standardized error codes and retry strategies for MARS integration
Per management directive - critical for Subgraph error handling
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Standardized error codes that MARS Subgraphs expect (per Contract v1.0)"""

    # Contract-required error codes
    CAPABILITY_NOT_FOUND = "CAPABILITY_NOT_FOUND"
    CREDENTIALS_MISSING = "CREDENTIALS_MISSING"
    CREDENTIALS_INVALID = "CREDENTIALS_INVALID"
    CREDENTIALS_INSUFFICIENT = "CREDENTIALS_INSUFFICIENT"
    RATE_LIMIT = "RATE_LIMIT"
    NETWORK_ERROR = "NETWORK_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # Legacy codes (backward compatibility - will be deprecated)
    CREDENTIAL_MISSING = "CREDENTIALS_MISSING"  # Alias for CREDENTIALS_MISSING
    CREDENTIAL_INVALID = "CREDENTIALS_INVALID"  # Alias for CREDENTIALS_INVALID
    API_DOWN = "NETWORK_ERROR"  # Alias for NETWORK_ERROR
    MISSING_PERMISSION = "PERMISSION_DENIED"  # Alias for PERMISSION_DENIED
    NOT_FOUND = "CAPABILITY_NOT_FOUND"  # Alias for CAPABILITY_NOT_FOUND
    INTERNAL_STARGATE_ERROR = "EXECUTION_ERROR"  # Alias for EXECUTION_ERROR
    EXTERNAL_API_ERROR = "EXECUTION_ERROR"  # Alias for EXECUTION_ERROR


class RetryStrategy(str, Enum):
    """Retry strategies that MARS should follow"""

    HUMAN_INTERVENTION = "human_intervention"  # User must fix (reconnect, grant permission)
    BACKOFF = "backoff"  # Retry with exponential backoff
    NONE = "none"  # Do not retry


# Mapping of error codes to retry strategies (per Stargate Command Contract v1.0)
ERROR_RETRY_STRATEGIES: dict[ErrorCode, RetryStrategy] = {
    # Contract-required codes
    ErrorCode.CAPABILITY_NOT_FOUND: RetryStrategy.NONE,
    ErrorCode.CREDENTIALS_MISSING: RetryStrategy.HUMAN_INTERVENTION,
    ErrorCode.CREDENTIALS_INVALID: RetryStrategy.HUMAN_INTERVENTION,
    ErrorCode.CREDENTIALS_INSUFFICIENT: RetryStrategy.HUMAN_INTERVENTION,
    ErrorCode.RATE_LIMIT: RetryStrategy.BACKOFF,
    ErrorCode.NETWORK_ERROR: RetryStrategy.BACKOFF,
    ErrorCode.VALIDATION_ERROR: RetryStrategy.NONE,
    ErrorCode.EXECUTION_ERROR: RetryStrategy.BACKOFF,
    ErrorCode.QUOTA_EXCEEDED: RetryStrategy.HUMAN_INTERVENTION,
    ErrorCode.PERMISSION_DENIED: RetryStrategy.HUMAN_INTERVENTION,
}


class StargateError(Exception):
    """
    Base exception for all Stargate errors
    Automatically includes error_code and retry_strategy in response
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: dict[str, Any] | None = None,
        http_status: int = 500,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.retry_strategy = ERROR_RETRY_STRATEGIES[error_code]
        self.details = details or {}
        self.http_status = http_status

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response (per Stargate Command Contract v1.0)"""
        return {
            "status": "error",  # Contract-compliant: always "error"
            "error_code": self.error_code.value,
            "error_message": self.message,
            "details": self.details,
            # Note: capability_key, timestamp, logs added by caller (main.py)
        }


# Specific error classes for common scenarios (updated to use contract-compliant error codes)


class CapabilityNotFoundError(StargateError):
    """Capability key not found in registry"""

    def __init__(self, capability_key: str) -> None:
        super().__init__(
            message=f"Capability not found: '{capability_key}'",
            error_code=ErrorCode.CAPABILITY_NOT_FOUND,
            details={"capability_key": capability_key},
            http_status=200,  # Contract: Always return HTTP 200 with status:"error"
        )


class CredentialMissingError(StargateError):
    """User has not connected this service (updated to use CREDENTIALS_MISSING)"""

    def __init__(self, service: str, org_id: str, user_id: str) -> None:
        msg = f"No credentials found for service '{service}' (org={org_id}, user={user_id})"
        super().__init__(
            message=msg,
            error_code=ErrorCode.CREDENTIALS_MISSING,
            details={"service": service, "org_id": org_id, "user_id": user_id},
            http_status=200,
        )


class CredentialInvalidError(StargateError):
    """Credentials expired or revoked (updated to use CREDENTIALS_INVALID)"""

    def __init__(self, service: str, reason: str = "Token expired or revoked") -> None:
        super().__init__(
            message=f"Invalid credentials for service '{service}': {reason}",
            error_code=ErrorCode.CREDENTIALS_INVALID,
            details={"service": service, "reason": reason},
            http_status=200,
        )


class CredentialsInsufficientError(StargateError):
    """User needs additional OAuth scopes"""

    def __init__(self, service: str, required_scopes: list[str]) -> None:
        msg = (
            f"Insufficient credentials for service '{service}': "
            f"missing scopes {required_scopes}"
        )
        super().__init__(
            message=msg,
            error_code=ErrorCode.CREDENTIALS_INSUFFICIENT,
            details={"service": service, "required_scopes": required_scopes},
            http_status=200,
        )


class RateLimitError(StargateError):
    """API rate limit exceeded"""

    def __init__(self, service: str, retry_after: int | None = None) -> None:
        details: dict[str, Any] = {"service": service}
        if retry_after:
            details["retry_after_seconds"] = retry_after

        super().__init__(
            message=f"Rate limit exceeded for service '{service}'",
            error_code=ErrorCode.RATE_LIMIT,
            details=details,
            http_status=200,
        )


class NetworkError(StargateError):
    """Network failure to external API (replaces APIDownError)"""

    def __init__(self, service: str, status_code: int | None = None) -> None:
        details: dict[str, Any] = {"service": service}
        if status_code:
            details["external_status_code"] = status_code

        super().__init__(
            message=f"Network error connecting to service '{service}'",
            error_code=ErrorCode.NETWORK_ERROR,
            details=details,
            http_status=200,
        )


class PermissionDeniedError(StargateError):
    """User lacks required permissions (replaces MissingPermissionError)"""

    def __init__(self, service: str, required_scope: str) -> None:
        super().__init__(
            message=f"Permission denied for service '{service}': {required_scope}",
            error_code=ErrorCode.PERMISSION_DENIED,
            details={"service": service, "required_scope": required_scope},
            http_status=200,
        )


# Legacy aliases (backward compatibility)
APIDownError = NetworkError
MissingPermissionError = PermissionDeniedError


class ValidationError(StargateError):
    """Input data from MIND/Subgraph was invalid"""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(
            message=f"Validation error on field '{field}': {reason}",
            error_code=ErrorCode.VALIDATION_ERROR,
            details={"field": field, "reason": reason},
            http_status=200,
        )


class ExecutionError(StargateError):
    """Tool execution failed (generic)"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=f"Execution error: {message}",
            error_code=ErrorCode.EXECUTION_ERROR,
            details=details or {},
            http_status=200,
        )


class QuotaExceededError(StargateError):
    """External service quota exceeded"""

    def __init__(self, service: str, quota_type: str) -> None:
        super().__init__(
            message=f"Quota exceeded for service '{service}': {quota_type}",
            error_code=ErrorCode.QUOTA_EXCEEDED,
            details={"service": service, "quota_type": quota_type},
            http_status=200,
        )


# Legacy error classes (backward compatibility)


class NotFoundError(StargateError):
    """Resource does not exist (maps to CAPABILITY_NOT_FOUND)"""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            error_code=ErrorCode.CAPABILITY_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
            http_status=200,
        )


class InternalStargateError(StargateError):
    """Internal Stargate error (maps to EXECUTION_ERROR)"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=f"Internal Stargate error: {message}",
            error_code=ErrorCode.EXECUTION_ERROR,
            details=details,
            http_status=200,
        )


class ExternalAPIError(StargateError):
    """Generic error from external API (maps to EXECUTION_ERROR)"""

    def __init__(self, service: str, status_code: int, message: str) -> None:
        super().__init__(
            message=f"External API error from '{service}': {message}",
            error_code=ErrorCode.EXECUTION_ERROR,
            details={
                "service": service,
                "external_status_code": status_code,
                "external_message": message,
            },
            http_status=200,
        )


def classify_exception(exception: Exception, service: str) -> StargateError:
    """
    Helper function to classify generic exceptions into Stargate error taxonomy
    Use this in try/except blocks to convert external API errors
    Updated to use contract-compliant error codes
    """
    error_message = str(exception)

    # Already a StargateError
    if isinstance(exception, StargateError):
        return exception

    # Check for common patterns in error messages
    error_lower = error_message.lower()
    if "credential" in error_lower or "authentication" in error_lower:
        if "not found" in error_message.lower() or "missing" in error_message.lower():
            return CredentialMissingError(service, "unknown", "unknown")
        elif "insufficient" in error_message.lower() or "scope" in error_message.lower():
            return CredentialsInsufficientError(service, ["unknown"])
        else:
            return CredentialInvalidError(service, error_message)

    if "rate limit" in error_message.lower() or "429" in error_message:
        return RateLimitError(service)

    if "quota" in error_message.lower() or "limit exceeded" in error_message.lower():
        return QuotaExceededError(service, "unknown")

    if "503" in error_message or "unavailable" in error_lower or "network" in error_lower:
        return NetworkError(service)

    if "permission" in error_lower or "403" in error_message or "forbidden" in error_lower:
        return PermissionDeniedError(service, "unknown")

    if "not found" in error_lower or "404" in error_message:
        return CapabilityNotFoundError("unknown")

    if "validation" in error_lower or "invalid input" in error_lower:
        return ValidationError("unknown", error_message)

    # Default to execution error (generic tool failure)
    return ExecutionError(
        error_message, {"service": service, "exception_type": type(exception).__name__}
    )


# ========== UTILITY-SPECIFIC ERRORS ==========


class ProviderUnavailableError(StargateError):
    """All providers for a utility are unavailable (rate limited, network error)"""

    def __init__(self, utility: str, providers_tried: list[str]) -> None:
        msg = f"All providers unavailable for utility '{utility}': " f"tried {providers_tried}"
        super().__init__(
            message=msg,
            error_code=ErrorCode.NETWORK_ERROR,
            details={"utility": utility, "providers_tried": providers_tried},
            http_status=200,
        )


class ContentTooLargeError(StargateError):
    """Input content exceeds utility limits"""

    def __init__(self, utility: str, max_size: int, actual_size: int, unit: str = "bytes") -> None:
        msg = f"Content exceeds {utility} limit: {actual_size} {unit} > {max_size} {unit}"
        super().__init__(
            message=msg,
            error_code=ErrorCode.VALIDATION_ERROR,
            details={
                "utility": utility,
                "max_size": max_size,
                "actual_size": actual_size,
                "unit": unit,
            },
            http_status=200,
        )


class UnsafeContentError(StargateError):
    """Content flagged as unsafe by provider safety filter"""

    def __init__(self, utility: str, reason: str) -> None:
        super().__init__(
            message=f"Content flagged as unsafe by {utility}: {reason}",
            error_code=ErrorCode.VALIDATION_ERROR,
            details={"utility": utility, "safety_reason": reason},
            http_status=200,
        )
