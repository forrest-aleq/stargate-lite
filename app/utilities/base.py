"""
Base utility class for Stargate Lite cognitive utilities.

Provides common patterns for:
- Lazy initialization of API clients
- API key management from environment variables
- Cost and usage tracking
- Structured error handling
- Provider fallback logic
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, ClassVar, TypedDict


class UtilityMetrics(TypedDict):
    """Type for utility metrics dictionary."""

    total_calls: int
    total_cost_usd: float
    total_tokens_input: int
    total_tokens_output: int
    first_call_at: str | None
    last_call_at: str | None


from app.errors import (
    CredentialMissingError,
    ExecutionError,
    NetworkError,
    RateLimitError,
)
from app.logging_config import get_logger

logger = get_logger(__name__)


class BaseUtility(ABC):
    """
    Abstract base class for all Stargate utilities.

    Design principles:
    1. Lazy initialization - don't load heavy dependencies until first use
    2. Fail-fast - validate API keys early, raise clear errors
    3. Cost tracking - utilities often have per-call costs
    4. Structured output - all methods return Dict with consistent schema

    Subclasses must:
    - Set SERVICE_NAME class attribute
    - Set REQUIRED_ENV_VARS list (can be empty)
    - Implement _initialize_client() method
    """

    # Override in subclass
    SERVICE_NAME: ClassVar[str] = "utility"
    REQUIRED_ENV_VARS: ClassVar[list[str]] = []

    def __init__(self) -> None:
        self._initialized = False
        self._api_keys: dict[str, str] = {}
        self._client: Any = None
        self.metrics: UtilityMetrics = {
            "total_calls": 0,
            "total_cost_usd": 0.0,
            "total_tokens_input": 0,
            "total_tokens_output": 0,
            "first_call_at": None,
            "last_call_at": None,
        }

    def _ensure_initialized(self) -> None:
        """
        Lazy initialization - validates API keys and initializes client.
        Call this at the start of each public method.
        """
        if self._initialized:
            return

        # Validate and store required environment variables
        missing_vars = []
        for env_var in self.REQUIRED_ENV_VARS:
            value = os.getenv(env_var)
            if not value:
                missing_vars.append(env_var)
            else:
                self._api_keys[env_var] = value

        if missing_vars:
            logger.error(
                f"Missing required environment variables for {self.SERVICE_NAME}",
                service=self.SERVICE_NAME,
                missing_vars=missing_vars,
                log_event="utility_init_error",
            )
            raise CredentialMissingError(
                service=self.SERVICE_NAME, org_id="AGENT", user_id="SYSTEM"
            )

        # Initialize the client (subclass implementation)
        try:
            self._initialize_client()
            self._initialized = True
            logger.info(
                f"{self.SERVICE_NAME} utility initialized",
                service=self.SERVICE_NAME,
                log_event="utility_init_success",
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize {self.SERVICE_NAME} utility",
                service=self.SERVICE_NAME,
                error_type=type(e).__name__,
                log_event="utility_init_error",
                exc_info=True,
            )
            raise ExecutionError(
                f"Failed to initialize {self.SERVICE_NAME}: {e!s}",
                details={"service": self.SERVICE_NAME, "error": str(e)},
            ) from e

    @abstractmethod
    def _initialize_client(self) -> None:
        """
        Initialize API client - override in subclass.
        Called once during lazy initialization.
        Store client in self._client if needed.
        """
        pass

    def _track_usage(self, tokens_in: int = 0, tokens_out: int = 0, cost_usd: float = 0.0) -> None:
        """
        Track API usage for cost monitoring.
        Call this after each successful API call.
        """
        now = datetime.utcnow().isoformat()

        self.metrics["total_calls"] += 1
        self.metrics["total_tokens_input"] += tokens_in
        self.metrics["total_tokens_output"] += tokens_out
        self.metrics["total_cost_usd"] += cost_usd
        self.metrics["last_call_at"] = now

        if self.metrics["first_call_at"] is None:
            self.metrics["first_call_at"] = now

        logger.info(
            "Utility usage tracked",
            service=self.SERVICE_NAME,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            total_calls=self.metrics["total_calls"],
            total_cost=self.metrics["total_cost_usd"],
            log_event="utility_usage",
        )

    def get_metrics(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Return usage metrics for this utility instance.
        Registered as a capability for monitoring.
        """
        return {"service": self.SERVICE_NAME, "metrics": self.metrics.copy(), "status": "success"}


class MultiProviderUtility(BaseUtility):
    """
    Base class for utilities with multiple provider options.
    Provides automatic fallback when primary provider fails.

    Subclasses must:
    - Set PROVIDERS list: [("name", "ENV_VAR_NAME"), ...]
    - Implement _call_{provider_name}() for each provider
    """

    # Override in subclass: [("tavily", "TAVILY_API_KEY"), ("serper", "SERPER_API_KEY")]
    PROVIDERS: ClassVar[list[tuple[str, str]]] = []

    def __init__(self) -> None:
        super().__init__()
        self._available_providers: list[str] = []

    def _initialize_client(self) -> None:
        """Initialize by checking which providers are available."""
        for provider_name, env_var in self.PROVIDERS:
            api_key = os.getenv(env_var)
            if api_key:
                self._available_providers.append(provider_name)
                self._api_keys[env_var] = api_key

        if not self._available_providers:
            raise CredentialMissingError(
                service=self.SERVICE_NAME, org_id="AGENT", user_id="SYSTEM"
            )

        logger.info(
            f"{self.SERVICE_NAME} initialized with providers",
            service=self.SERVICE_NAME,
            providers=self._available_providers,
            log_event="utility_init_success",
        )

    def _call_with_fallback(self, method_name: str, **kwargs: Any) -> dict[str, Any]:
        """
        Try providers in order, falling back on failure.
        Returns result with 'provider_used' field.
        """
        errors = []

        for provider_name in self._available_providers:
            try:
                # Get provider-specific method
                method = getattr(self, f"_call_{provider_name}", None)
                if not method:
                    logger.warning(
                        f"Provider method not implemented: _call_{provider_name}",
                        service=self.SERVICE_NAME,
                        provider=provider_name,
                    )
                    continue

                result: dict[str, Any] = method(**kwargs)
                result["provider_used"] = provider_name
                return result

            except RateLimitError as e:
                logger.warning(
                    f"Rate limited by {provider_name}, trying next provider",
                    service=self.SERVICE_NAME,
                    provider=provider_name,
                    log_event="provider_rate_limited",
                )
                errors.append((provider_name, "rate_limited", str(e)))
                continue

            except NetworkError as e:
                logger.warning(
                    f"Network error with {provider_name}, trying next provider",
                    service=self.SERVICE_NAME,
                    provider=provider_name,
                    error=str(e),
                    log_event="provider_network_error",
                )
                errors.append((provider_name, "network_error", str(e)))
                continue

            except Exception as e:
                logger.warning(
                    f"Error with {provider_name}, trying next provider",
                    service=self.SERVICE_NAME,
                    provider=provider_name,
                    error_type=type(e).__name__,
                    error=str(e),
                    log_event="provider_error",
                )
                errors.append((provider_name, type(e).__name__, str(e)))
                continue

        # All providers failed
        logger.error(
            f"All providers failed for {self.SERVICE_NAME}",
            service=self.SERVICE_NAME,
            errors=errors,
            log_event="all_providers_failed",
        )

        from app.errors import ProviderUnavailableError

        raise ProviderUnavailableError(
            utility=self.SERVICE_NAME, providers_tried=[e[0] for e in errors]
        )
