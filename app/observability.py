"""
Observability configuration for Stargate Lite
Logging and metrics setup for DataDog integration
Call setup_logging() from FastAPI startup event to configure after uvicorn starts
"""

import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path

from datadog import statsd


def setup_logging() -> None:
    """
    Configure logging handlers for the application.
    Must be called AFTER uvicorn starts (in FastAPI startup event)
    to prevent uvicorn from clearing our handlers.

    Includes defensive error handling to gracefully degrade to console-only logging
    if file logging cannot be configured.
    """
    # Determine if we're in a monitored environment (matches regular stargate pattern)
    is_datadog_enabled = os.getenv("DD_ENABLED", "false").lower() == "true"
    is_monitored_env = os.getenv("DD_ENV") in ("production", "staging")
    should_log_to_file = is_datadog_enabled and is_monitored_env

    # Get root logger
    root_logger = logging.getLogger()

    # Don't change the level - uvicorn already set it
    # Just add our file handler to uvicorn's existing handlers

    # Define log format (ddtrace will inject trace/span IDs automatically)
    log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # File handler (for DataDog agent to read) - only in monitored environments
    if should_log_to_file:
        log_dir = None

        # Try to create logs directory with fallback to temp directory
        try:
            log_dir = Path("/app/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            # Fallback to temp directory if /app/logs is not writable
            try:
                log_dir = Path(tempfile.gettempdir()) / "stargate-logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                logging.warning(f"Could not create /app/logs ({e}), using fallback: {log_dir}")
            except Exception as fallback_error:
                logging.warning(
                    f"Could not create log directory ({fallback_error}), "
                    "continuing with console-only logging"
                )
                log_dir = None

        # Try to add file handler if we have a valid log directory
        if log_dir:
            try:
                file_handler = RotatingFileHandler(
                    log_dir / "application.log",
                    maxBytes=10_000_000,  # 10MB
                    backupCount=5,
                )
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(log_format)
                root_logger.addHandler(file_handler)

                # Log that file logging is enabled
                logger = logging.getLogger(__name__)
                log_path = log_dir / "application.log"
                dd_env = os.getenv("DD_ENV")
                logger.info(
                    f"File logging enabled - writing to {log_path} "
                    f"(DD_ENABLED={is_datadog_enabled}, DD_ENV={dd_env})"
                )
            except (OSError, PermissionError) as e:
                # If file handler creation fails, log warning and continue with console-only
                logging.warning(
                    f"Could not create file handler ({e}), " "continuing with console-only logging"
                )


def increment_metric(metric_name: str, tags: list[str] | None = None) -> None:
    """
    Wrapper for statsd.increment that automatically adds environment and service tags.

    Args:
        metric_name: The metric name to increment (e.g., 'stargate_lite.health_check.called')
        tags: Optional list of additional tags to include
    """
    dd_env = os.getenv("DD_ENV", "staging")
    dd_service = os.getenv("DD_SERVICE", "stargate-lite")

    # Base tags that should always be present
    base_tags = [f"environment:{dd_env}", f"service:{dd_service}"]

    # Merge with additional tags if provided
    all_tags = base_tags + (tags or [])

    statsd.increment(metric_name, tags=all_tags)
