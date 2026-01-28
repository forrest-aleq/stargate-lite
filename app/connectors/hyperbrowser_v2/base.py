"""
Base class for Hyperbrowser v2 connector with core execution loop.
"""

import os
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from anthropic import Anthropic

from app.logging_config import get_logger

from .environment import BrowserExecutionEnvironment

logger = get_logger(__name__)


class HyperbrowserBase:
    """
    Base class with initialization and core execution loop.

    REQUIREMENTS:
    - ANTHROPIC_API_KEY in environment
    - Execution environment (Docker/VM/cloud service)
    """

    def __init__(self, execution_env: BrowserExecutionEnvironment | None = None):
        # API client
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client: Anthropic | None = None  # Lazy init
        self.model = "claude-sonnet-4-20250514"
        self.beta_version = "computer-use-2025-01-24"

        # Execution environment
        self.execution_env = execution_env

        # Display settings
        self.display_width = 1280
        self.display_height = 800

        # Session management
        self.conversation_history: list[dict[str, Any]] = []
        self.action_log: list[dict[str, Any]] = []  # Audit trail
        self.max_iterations = 50  # Safety limit

        # Performance tracking
        self.metrics = {
            "total_actions": 0,
            "api_calls": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
        }

    def _ensure_client(self) -> None:
        """Lazy initialization of Anthropic client"""
        if self.client is None:
            if not self.api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. Add to .env file:\nANTHROPIC_API_KEY=sk-ant-..."
                )
            self.client = Anthropic(api_key=self.api_key)

    def _ensure_execution_env(self) -> None:
        """Ensure execution environment is configured"""
        if self.execution_env is None:
            raise ValueError(
                "Browser execution environment not configured.\n"
                "See documentation for setting up Docker container or cloud service."
            )

    def _build_initial_message(self, goal: str, screenshot: str) -> list[dict[str, Any]]:
        """Build initial conversation message with screenshot and goal."""
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": screenshot},
                    },
                    {
                        "type": "text",
                        "text": f"Goal: {goal}\n\nTake the next action to achieve this goal.",
                    },
                ],
            }
        ]

    def _call_claude_for_action(self, messages: list[dict[str, Any]]) -> Any:
        """Call Claude API to decide next action."""
        assert self.client is not None
        return self.client.beta.messages.create(
            model=self.model,
            max_tokens=4096,
            tools=[
                {
                    "type": "computer_20250124",
                    "name": "computer",
                    "display_width_px": self.display_width,
                    "display_height_px": self.display_height,
                }
            ],
            messages=messages,
            betas=[self.beta_version],
        )

    def _handle_completion(
        self,
        response: Any,
        iteration: int,
        action_log: list[dict[str, Any]],
        current_screenshot: str,
        validate_result: Callable[[str, str], bool] | None,
    ) -> dict[str, Any] | None:
        """Handle end_turn response from Claude. Returns result dict or None to continue."""
        final_text = ""
        for block in response.content:
            if block.type == "text":
                final_text += block.text

        action_log.append(
            {
                "iteration": iteration,
                "type": "completion",
                "message": final_text,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        if validate_result and not validate_result(final_text, current_screenshot):
            action_log.append(
                {
                    "iteration": iteration,
                    "type": "validation_failed",
                    "message": "Goal not achieved per validation function",
                }
            )
            return {
                "status": "validation_failed",
                "iterations": iteration,
                "action_log": action_log,
                "final_screenshot": current_screenshot,
                "result": final_text,
            }

        return {
            "status": "success",
            "iterations": iteration,
            "action_log": action_log,
            "final_screenshot": current_screenshot,
            "result": final_text,
        }

    def _execute_single_action(
        self,
        block: Any,
        action_log: list[dict[str, Any]],
        iteration: int,
        api_latency: float,
        current_screenshot: str,
    ) -> tuple[dict[str, Any], str]:
        """Execute a single tool use action. Returns (tool_result, new_screenshot)."""
        assert self.execution_env is not None
        action_input = block.input

        action_log.append(
            {
                "iteration": iteration,
                "tool_use_id": block.id,
                "action": action_input.get("action"),
                "input": action_input,
                "timestamp": datetime.utcnow().isoformat(),
                "api_latency_ms": api_latency,
            }
        )

        exec_start = time.time()
        try:
            exec_result = self.execution_env.execute_action(action_input)
            exec_latency = (time.time() - exec_start) * 1000

            if action_input.get("action") != "screenshot":
                new_screenshot = self.execution_env.take_screenshot()
            else:
                new_screenshot = str(exec_result.get("screenshot", ""))

            tool_result = {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": new_screenshot,
                        },
                    }
                ],
            }

            action_log[-1]["execution_latency_ms"] = exec_latency
            action_log[-1]["success"] = True
            self.metrics["total_actions"] += 1

            return tool_result, new_screenshot

        except Exception as e:
            action_log[-1]["success"] = False
            action_log[-1]["error"] = str(e)

            tool_result = {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": f"Error executing action: {e!s}",
                "is_error": True,
            }
            return tool_result, current_screenshot

    def _process_tool_uses(
        self,
        response: Any,
        action_log: list[dict[str, Any]],
        iteration: int,
        api_latency: float,
        current_screenshot: str,
    ) -> tuple[list[dict[str, Any]], str]:
        """Process all tool uses in response. Returns (tool_results, updated_screenshot)."""
        tool_results = []
        screenshot = current_screenshot

        for block in response.content:
            if block.type == "tool_use":
                tool_result, screenshot = self._execute_single_action(
                    block, action_log, iteration, api_latency, screenshot
                )
                tool_results.append(tool_result)

        return tool_results, screenshot

    def _execute_action_loop(
        self,
        goal: str,
        initial_screenshot: str | None = None,
        max_iterations: int | None = None,
        validate_result: Callable[[str, str], bool] | None = None,
    ) -> dict[str, Any]:
        """
        Core execution loop: Screenshot -> Claude -> Action -> Execute -> Repeat

        Args:
            goal: What to accomplish (e.g., "Export Power BI report to Excel")
            initial_screenshot: Optional starting screenshot (otherwise takes one)
            max_iterations: Max iterations (default: self.max_iterations)
            validate_result: Optional function to validate if goal achieved

        Returns:
            Dict with execution results, final screenshot, action log
        """
        self._ensure_client()
        self._ensure_execution_env()
        assert self.execution_env is not None

        max_iter = max_iterations or self.max_iterations
        current_screenshot = initial_screenshot or self.execution_env.take_screenshot()
        messages = self._build_initial_message(goal, current_screenshot)
        action_log: list[dict[str, Any]] = []

        for iteration in range(1, max_iter + 1):
            start_time = time.time()
            response = self._call_claude_for_action(messages)
            api_latency = (time.time() - start_time) * 1000
            self.metrics["api_calls"] += 1

            if response.stop_reason == "end_turn":
                result = self._handle_completion(
                    response, iteration, action_log, current_screenshot, validate_result
                )
                if result is not None:
                    return result

            tool_results, current_screenshot = self._process_tool_uses(
                response, action_log, iteration, api_latency, current_screenshot
            )

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        action_log.append(
            {
                "iteration": max_iter,
                "type": "max_iterations_reached",
                "message": f"Stopped after {max_iter} iterations",
            }
        )

        return {
            "status": "max_iterations",
            "iterations": max_iter,
            "action_log": action_log,
            "final_screenshot": current_screenshot,
            "result": "Max iterations reached without completion",
        }
