"""
Base class for Hyperbrowser v2 connector using Hyperbrowser Cloud API.

Uses the Hyperbrowser managed Claude Computer Use agent for all browser
automation. The managed agent handles the screenshot→Claude→action→screenshot
loop on Hyperbrowser's infrastructure in isolated containers.
"""

import os
from typing import Any

from hyperbrowser import Hyperbrowser
from hyperbrowser.models.agents.claude_computer_use import (
    StartClaudeComputerUseTaskParams,
)
from hyperbrowser.models.session import CreateSessionParams

from app.logging_config import get_logger

logger = get_logger(__name__)


class HyperbrowserBase:
    """
    Base class with Hyperbrowser Cloud client and task execution.

    REQUIREMENTS:
    - HYPERBROWSER_API_KEY in environment

    NOTE: Anthropic model access is handled by Hyperbrowser's infrastructure.
    We use Azure AI Foundry for our own Anthropic calls (summarizer, etc.),
    but Hyperbrowser's managed agent uses their own Anthropic access.
    """

    def __init__(self) -> None:
        self.hyperbrowser_api_key = os.getenv("HYPERBROWSER_API_KEY")
        self.client: Hyperbrowser | None = None  # Lazy init

        # Session management
        self._session_id: str | None = None
        self.action_log: list[dict[str, Any]] = []
        self.max_steps = 50  # Safety limit

        # Performance tracking
        self.metrics: dict[str, Any] = {
            "total_tasks": 0,
            "api_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
        }

    def _ensure_client(self) -> None:
        """Lazy initialization of Hyperbrowser client."""
        if self.client is None:
            if not self.hyperbrowser_api_key:
                raise ValueError(
                    "HYPERBROWSER_API_KEY not set. " "Get your key at https://app.hyperbrowser.ai/"
                )
            self.client = Hyperbrowser(api_key=self.hyperbrowser_api_key)

    def _create_session(self, **kwargs: Any) -> str:
        """Create a new Hyperbrowser browser session.

        Returns:
            Session ID for use in subsequent operations.
        """
        self._ensure_client()
        assert self.client is not None

        params = CreateSessionParams(**kwargs) if kwargs else None
        session = self.client.sessions.create(params=params)
        session_id: str = session.id
        self._session_id = session_id

        logger.info(
            "Hyperbrowser session created",
            session_id=session_id,
            log_event="hyperbrowser_session_create",
        )

        return session_id

    def _stop_session(self) -> None:
        """Stop the current Hyperbrowser session."""
        if self.client is not None and self._session_id is not None:
            try:
                self.client.sessions.stop(self._session_id)
                logger.info(
                    "Hyperbrowser session stopped",
                    session_id=self._session_id,
                    log_event="hyperbrowser_session_stop",
                )
            except Exception as e:
                logger.warning(
                    "Failed to stop Hyperbrowser session",
                    session_id=self._session_id,
                    error=str(e),
                    log_event="hyperbrowser_session_stop_error",
                )
            finally:
                self._session_id = None

    def _take_screenshot(self) -> str:
        """Take a screenshot of the current browser session.

        Returns:
            Base64-encoded PNG screenshot, or empty string on failure.
        """
        self._ensure_client()
        assert self.client is not None

        if self._session_id is None:
            return ""

        try:
            result = self.client.computer_action.screenshot(self._session_id)
            return result.screenshot or ""
        except Exception as e:
            logger.warning(
                "Failed to take screenshot",
                session_id=self._session_id,
                error=str(e),
                log_event="hyperbrowser_screenshot_error",
            )
            return ""

    def _run_task(
        self,
        goal: str,
        max_steps: int | None = None,
        keep_browser_open: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a browser task via Hyperbrowser's managed Claude Computer Use agent.

        This replaces the old screenshot→Claude→action loop. Hyperbrowser handles
        the entire execution on their infrastructure.

        Args:
            goal: Natural language description of what to accomplish.
            max_steps: Max agent steps (default: self.max_steps).
            keep_browser_open: Keep session alive after task completes.

        Returns:
            Dict with status, result, iterations, action_log, final_screenshot.
        """
        self._ensure_client()
        assert self.client is not None

        steps = max_steps or self.max_steps

        logger.info(
            "Starting Hyperbrowser task",
            goal=goal[:200],
            max_steps=steps,
            session_id=self._session_id,
            log_event="hyperbrowser_task_start",
        )

        try:
            params = StartClaudeComputerUseTaskParams(
                task=goal,
                max_steps=steps,
                session_id=self._session_id,
                keep_browser_open=keep_browser_open,
            )

            result = self.client.agents.claude_computer_use.start_and_wait(params)

            # Track session ID from the task if we don't have one
            self.metrics["api_calls"] += 1
            self.metrics["total_tasks"] += 1

            if result.metadata:
                self.metrics["total_input_tokens"] += result.metadata.input_tokens or 0
                self.metrics["total_output_tokens"] += result.metadata.output_tokens or 0

            completed_steps = result.metadata.num_task_steps_completed if result.metadata else None

            if result.status == "completed" and result.data and result.data.final_result:
                logger.info(
                    "Hyperbrowser task completed",
                    status="success",
                    steps_completed=completed_steps,
                    log_event="hyperbrowser_task_success",
                )
                return {
                    "status": "success",
                    "result": result.data.final_result,
                    "iterations": completed_steps or steps,
                    "action_log": [],
                    "final_screenshot": "",
                }

            if result.status == "failed":
                logger.warning(
                    "Hyperbrowser task failed",
                    error=result.error,
                    log_event="hyperbrowser_task_error",
                )
                return {
                    "status": "error",
                    "result": result.error or "Task failed",
                    "iterations": completed_steps or 0,
                    "action_log": [],
                    "final_screenshot": "",
                }

            # Completed but no final result (max steps reached or stopped)
            final_text = ""
            if result.data and result.data.final_result:
                final_text = result.data.final_result

            logger.info(
                "Hyperbrowser task ended",
                status=result.status,
                steps_completed=completed_steps,
                log_event="hyperbrowser_task_success",
            )
            return {
                "status": "max_iterations" if result.status != "completed" else "success",
                "result": final_text or "Task completed without explicit result",
                "iterations": completed_steps or steps,
                "action_log": [],
                "final_screenshot": "",
            }

        except Exception as e:
            logger.error(
                "Hyperbrowser task error",
                error=str(e),
                goal=goal[:200],
                log_event="hyperbrowser_task_error",
            )
            return {
                "status": "error",
                "result": f"Hyperbrowser task error: {e!s}",
                "iterations": 0,
                "action_log": [],
                "final_screenshot": "",
            }
