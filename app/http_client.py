"""
Centralized HTTP client for Stargate connectors

Provides:
- Automatic timeout protection (prevents hanging on slow APIs)
- Connection pooling (TCP connection reuse)
- JSON parsing safety (graceful handling of malformed responses)
- Retry logic with exponential backoff
- Error classification (maps HTTP codes to StargateError taxonomy)
- Metrics instrumentation
"""

import json
import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.errors import (
    CredentialInvalidError,
    ExecutionError,
    NetworkError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

logger = logging.getLogger("stargate.http_client")


class StargateHTTPClient:
    """Production-ready HTTP client with timeouts, retries, and error handling"""

    # Default timeouts: (connect_timeout, read_timeout) in seconds
    # Connect: 5s is sufficient for establishing TCP connection
    # Read: 30s allows for slow API responses but prevents indefinite hangs
    DEFAULT_TIMEOUT: tuple[int, int] = (5, 30)

    def __init__(self) -> None:
        """Initialize session with connection pooling and retry configuration"""
        self.session: requests.Session = requests.Session()

        # Configure retry strategy for transient failures
        # IMPORTANT: Only retry idempotent methods to avoid duplicate operations
        # POST/PUT/DELETE are excluded to prevent duplicate payments, resource creation, etc.
        retry_strategy = Retry(
            total=3,  # 3 retry attempts
            backoff_factor=0.5,  # Wait 0.5s, 1s, 2s between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
            allowed_methods=["GET", "HEAD", "OPTIONS"],  # Only idempotent methods
            raise_on_status=False,  # Don't raise exception, let us handle it
        )

        # Configure connection pooling
        adapter = HTTPAdapter(
            pool_connections=20,  # Number of connection pools to cache
            pool_maxsize=100,  # Max connections per pool
            max_retries=retry_strategy,
            pool_block=False,  # Don't block if pool exhausted, create new connection
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _handle_network_exception(
        self, exc: Exception, service: str, url: str, timeout: tuple[int, int] | None = None
    ) -> None:
        """Handle network-related exceptions and convert to StargateErrors.

        Args:
            exc: The caught exception
            service: Service name for error reporting
            url: The URL that was being requested
            timeout: The timeout tuple used for the request

        Raises:
            NetworkError: For timeout, connection, or SSL errors
            ExecutionError: For unexpected errors
        """
        if isinstance(exc, requests.exceptions.Timeout):
            logger.error(
                f"Request timeout to {service}",
                extra={"service": service, "url": url, "timeout": timeout},
            )
            raise NetworkError(service=service) from exc

        if isinstance(exc, requests.exceptions.ConnectionError):
            logger.error(
                f"Connection error to {service}",
                extra={"service": service, "url": url, "error": str(exc)},
            )
            raise NetworkError(service=service) from exc

        if isinstance(exc, requests.exceptions.SSLError):
            logger.error(
                f"SSL/TLS error for {service}",
                extra={"service": service, "url": url, "error": str(exc)},
            )
            raise NetworkError(service=service) from exc

        # Catch-all for unexpected errors
        logger.error(
            f"Unexpected HTTP error for {service}",
            extra={"service": service, "error": str(exc)},
            exc_info=True,
        )
        raise ExecutionError(
            f"Unexpected HTTP error: {exc!s}", details={"service": service, "url": url}
        ) from exc

    def _execute_request(
        self, method: str, url: str, service: str, timeout: tuple[int, int], **kwargs: Any
    ) -> requests.Response:
        """Execute the HTTP request with logging.

        Args:
            method: HTTP method
            url: Full URL to request
            service: Service name for logging
            timeout: Timeout tuple (connect, read)
            **kwargs: Additional arguments passed to requests.request()

        Returns:
            Response object from requests
        """
        logger.debug(
            f"HTTP {method} request to {service}",
            extra={"service": service, "url": url, "method": method},
        )

        return self.session.request(method=method, url=url, timeout=timeout, **kwargs)

    def request(
        self,
        method: str,
        url: str,
        service: str,
        timeout: tuple[int, int] | None = None,
        parse_json: bool = True,
        **kwargs: Any,
    ) -> Any:
        """
        Make HTTP request with automatic timeout, retry, and error handling

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            url: Full URL to request
            service: Service name for error reporting (e.g., "quickbooks", "hubspot")
            timeout: Optional custom timeout (connect, read) tuple
            parse_json: If True, automatically parse JSON response (default: True)
            **kwargs: Additional arguments passed to requests.request()

        Returns:
            Parsed JSON dict if parse_json=True, else Response object

        Raises:
            StargateError subclass based on response status code
        """
        timeout = timeout or self.DEFAULT_TIMEOUT

        try:
            response = self._execute_request(method, url, service, timeout, **kwargs)

            # Check for error status codes and classify
            if not response.ok:
                self._handle_error_response(response, service)

            # Parse JSON if requested
            if parse_json:
                return self._safe_json_parse(response, service)

            return response

        except (
            NetworkError,
            ExecutionError,
            CredentialInvalidError,
            PermissionDeniedError,
            NotFoundError,
            RateLimitError,
        ):
            # Re-raise our own exceptions without wrapping
            raise
        except Exception as e:
            # Handle network exceptions and unexpected errors
            self._handle_network_exception(e, service, url, timeout)

    def _safe_json_parse(self, response: requests.Response, service: str) -> dict[str, Any]:
        """
        Safely parse JSON response with error handling

        Args:
            response: Response object
            service: Service name for error reporting

        Returns:
            Parsed JSON dict

        Raises:
            ExecutionError: If JSON parsing fails
        """
        try:
            result: dict[str, Any] = response.json()
            return result
        except json.JSONDecodeError as e:
            # Log without content preview to prevent sensitive data leakage
            logger.error(
                f"JSON parsing failed for {service}",
                extra={
                    "service": service,
                    "status_code": response.status_code,
                    "content_length": len(response.text),
                    "content_type": response.headers.get("Content-Type", "unknown"),
                },
            )
            raise ExecutionError(
                f"Invalid JSON response from {service}",
                details={
                    "status_code": response.status_code,
                    "content_length": len(response.text),
                    "parse_error": str(e),
                },
            ) from e

    def _handle_error_response(self, response: requests.Response, service: str) -> None:
        """
        Classify HTTP error response into appropriate StargateError

        Maps HTTP status codes to Stargate error taxonomy for proper retry handling

        Args:
            response: Error response object
            service: Service name for error reporting

        Raises:
            StargateError subclass based on status code
        """
        status_code = response.status_code

        # Try to get error details from response body
        try:
            error_body = response.json()
            error_message = str(
                error_body.get("message") or error_body.get("error") or response.text[:500]
            )
        except (json.JSONDecodeError, ValueError):
            error_message = response.text[:500]  # Truncate to prevent log bloat

        logger.error(
            f"HTTP {status_code} error from {service}",
            extra={
                "service": service,
                "status_code": status_code,
                "error_message": error_message[:500],
            },
        )

        # Classify error by status code
        if status_code == 401:
            # Authentication failed - credential invalid or expired
            raise CredentialInvalidError(service=service, reason="Authentication failed")

        elif status_code == 403:
            # Permission denied - credential valid but lacks permissions
            raise PermissionDeniedError(service=service, required_scope=error_message[:200])

        elif status_code == 404:
            # Resource not found
            raise NotFoundError(resource_type="resource", resource_id="unknown")

        elif status_code == 429:
            # Rate limit exceeded
            retry_after_header = response.headers.get("Retry-After", "60")
            try:
                retry_after = int(retry_after_header)
            except ValueError:
                retry_after = 60

            raise RateLimitError(service=service, retry_after=retry_after)

        elif status_code >= 500:
            # Server error - retryable
            raise NetworkError(service=service, status_code=status_code)

        else:
            # Other client errors (400, 402, etc.)
            raise ExecutionError(
                f"HTTP {status_code} error from {service}",
                details={"status_code": status_code, "message": error_message[:500]},
            )

    def get(self, url: str, service: str, **kwargs: Any) -> dict[str, Any]:
        """Convenience method for GET requests"""
        result: dict[str, Any] = self.request("GET", url, service, **kwargs)
        return result

    def post(self, url: str, service: str, **kwargs: Any) -> dict[str, Any]:
        """Convenience method for POST requests"""
        result: dict[str, Any] = self.request("POST", url, service, **kwargs)
        return result

    def put(self, url: str, service: str, **kwargs: Any) -> dict[str, Any]:
        """Convenience method for PUT requests"""
        result: dict[str, Any] = self.request("PUT", url, service, **kwargs)
        return result

    def patch(self, url: str, service: str, **kwargs: Any) -> dict[str, Any]:
        """Convenience method for PATCH requests"""
        result: dict[str, Any] = self.request("PATCH", url, service, **kwargs)
        return result

    def delete(self, url: str, service: str, **kwargs: Any) -> dict[str, Any]:
        """Convenience method for DELETE requests"""
        result: dict[str, Any] = self.request("DELETE", url, service, **kwargs)
        return result


# Global singleton HTTP client instance
http_client = StargateHTTPClient()
