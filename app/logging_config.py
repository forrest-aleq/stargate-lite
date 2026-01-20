"""
Structured logging configuration for Stargate Lite

Provides JSON-formatted logs for production and human-readable logs for development.
Includes correlation IDs, request tracking, and contextual metadata.
"""

import logging
import os
import sys
from typing import Any

import structlog
from pythonjsonlogger import jsonlogger

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class ContextualJSONFormatter(jsonlogger.JsonFormatter):  # type: ignore[misc]
    """JSON formatter with additional context fields"""

    def add_fields(
        self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]
    ) -> None:
        """Add standardized fields to all log records"""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = record.created
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["service"] = "stargate-lite"
        log_record["environment"] = ENVIRONMENT

        # Add thread/process info for debugging
        log_record["thread_id"] = record.thread
        log_record["process_id"] = record.process


def configure_logging() -> None:
    """
    Configure structured logging for the application

    - Production (ENVIRONMENT=production): JSON-formatted logs to stdout
    - Development (ENVIRONMENT=development): Human-readable console logs with colors
    """

    # Clear any existing handlers
    logging.root.handlers = []

    # Configure structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if ENVIRONMENT == "production":
        # Production: JSON output
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

        # JSON formatter for stdlib logging
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            ContextualJSONFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        )

    else:
        # Development: Console output with colors
        processors = [*shared_processors, structlog.dev.ConsoleRenderer(colors=True)]

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)8s] %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )

    # Configure root logger
    logging.root.addHandler(handler)
    logging.root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", org_id="org_123", user_id="user_456")
    """
    return structlog.get_logger(name)


# Correlation ID management for request tracking
def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for the current context

    Note: This preserves existing context variables (org_id, user_id, etc.)
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def bind_request_context(
    org_id: str, user_id: str, capability_key: str, turn_id: str | None = None
) -> None:
    """
    Bind request-specific context to all logs

    Args:
        org_id: Organization ID
        user_id: User ID
        capability_key: Capability being executed
        turn_id: Optional turn ID for idempotency tracking
    """
    context = {"org_id": org_id, "user_id": user_id, "capability_key": capability_key}

    if turn_id:
        context["turn_id"] = turn_id
        # Use turn_id as correlation_id for request tracking
        context["correlation_id"] = turn_id

    structlog.contextvars.bind_contextvars(**context)


def clear_request_context() -> None:
    """Clear request-specific context"""
    structlog.contextvars.clear_contextvars()


# Initialize logging on module import
configure_logging()
