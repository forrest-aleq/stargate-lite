"""
Summarizer utility for Stargate Lite.

Provides text summarization capabilities via Claude (Anthropic).
Supports various summary styles: concise, executive, bullet points, key facts.

Capability keys:
- summarize.text: General text summarization
- summarize.executive: Executive summary format
- summarize.bullets: Bullet point extraction
- summarize.key_facts: Extract key facts and figures
"""

import json
from typing import Any, ClassVar

import anthropic

from app.errors import (
    ContentTooLargeError,
    ExecutionError,
    NetworkError,
    RateLimitError,
    ValidationError,
)
from app.logging_config import get_logger
from app.utilities.base import BaseUtility

logger = get_logger(__name__)


class SummarizerUtility(BaseUtility):
    """
    Text summarization utility using Claude.

    Uses Claude Haiku for cost-effective summarization.
    Falls back to Sonnet for complex documents.

    Supports:
    - Direct Anthropic API (ANTHROPIC_API_KEY)
    - Azure AI Foundry (ANTHROPIC_FOUNDRY_API_KEY + ANTHROPIC_FOUNDRY_RESOURCE)
    """

    SERVICE_NAME: ClassVar[str] = "summarizer"
    credential_type: ClassVar[str] = "agent"  # Uses Aleq's API keys, not customer OAuth
    # Support both direct Anthropic and Azure Foundry
    REQUIRED_ENV_VARS: ClassVar[list[str]] = []  # We'll check manually for flexibility

    # Token limits
    MAX_INPUT_TOKENS: ClassVar[int] = 100000  # ~75k words
    MAX_OUTPUT_TOKENS: ClassVar[int] = 4096

    # Pricing (per 1M tokens) - approximate for budgeting
    PRICING: ClassVar[dict[str, dict[str, float]]] = {
        "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
        "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku-20241022": {"input": 1.00, "output": 5.00},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    }

    def _initialize_client(self) -> None:
        """Initialize Anthropic client (supports Azure AI Foundry)."""
        import os

        # Check for Azure AI Foundry first
        foundry_key = os.getenv("ANTHROPIC_FOUNDRY_API_KEY")
        foundry_resource = os.getenv("ANTHROPIC_FOUNDRY_RESOURCE")

        if foundry_key and foundry_resource:
            # Azure AI Foundry configuration
            base_url = f"https://{foundry_resource}.services.ai.azure.com/anthropic"
            self._client = anthropic.Anthropic(api_key=foundry_key, base_url=base_url)
            # Use Azure model names
            self.DEFAULT_MODEL = os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL", "claude-haiku-4-5")
            self.COMPLEX_MODEL = os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-5")
            self._api_keys["ANTHROPIC_FOUNDRY_API_KEY"] = foundry_key
            logger.info(
                "Summarizer using Azure AI Foundry",
                service=self.SERVICE_NAME,
                resource=foundry_resource,
                default_model=self.DEFAULT_MODEL,
                log_event="foundry_client_init",
            )
        else:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                # Direct Anthropic API
                self._client = anthropic.Anthropic(api_key=api_key)
                self.DEFAULT_MODEL = "claude-3-5-haiku-20241022"
                self.COMPLEX_MODEL = "claude-3-5-sonnet-20241022"
                self._api_keys["ANTHROPIC_API_KEY"] = api_key
                logger.info(
                    "Summarizer using direct Anthropic API",
                    service=self.SERVICE_NAME,
                    log_event="anthropic_client_init",
                )
            else:
                from app.errors import CredentialMissingError

                raise CredentialMissingError(
                    service=self.SERVICE_NAME, org_id="AGENT", user_id="SYSTEM"
                )

    def summarize(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Summarize text content.

        Args:
            text: Text content to summarize (required)
            max_length: Target summary length in words (default 200)
            style: Summary style - "concise", "detailed", "executive" (default "concise")
            focus: Optional focus area for the summary
            language: Output language (default "english")

        Returns:
            summary: The generated summary
            word_count: Word count of summary
            input_tokens: Tokens consumed
            model_used: Model that generated the summary
        """
        self._ensure_initialized()

        text = args.get("text")
        if not text:
            raise ValidationError("text", "Text content is required")

        # Check length
        estimated_tokens = len(text) // 4
        if estimated_tokens > self.MAX_INPUT_TOKENS:
            raise ContentTooLargeError(
                utility=self.SERVICE_NAME,
                max_size=self.MAX_INPUT_TOKENS,
                actual_size=estimated_tokens,
                unit="tokens",
            )

        max_length = args.get("max_length", 200)
        style = args.get("style", "concise")
        focus = args.get("focus")
        language = args.get("language", "english")

        # Build prompt
        prompt = self._build_summary_prompt(text, max_length, style, focus, language)

        # Use Haiku for simple summaries, Sonnet for complex
        use_complex = style == "detailed" or estimated_tokens > 50000
        model = self.COMPLEX_MODEL if use_complex else self.DEFAULT_MODEL

        return self._call_claude(prompt, model, "summary")

    def executive_summary(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Generate executive summary with key takeaways.

        Args:
            text: Text content to summarize (required)
            audience: Target audience (default "executives")
            max_sections: Maximum number of sections (default 5)

        Returns:
            summary: Executive summary
            key_takeaways: List of key points
            recommendations: List of recommendations (if applicable)
        """
        self._ensure_initialized()

        text = args.get("text")
        if not text:
            raise ValidationError("text", "Text content is required")

        # Check length
        estimated_tokens = len(text) // 4
        if estimated_tokens > self.MAX_INPUT_TOKENS:
            raise ContentTooLargeError(
                utility=self.SERVICE_NAME,
                max_size=self.MAX_INPUT_TOKENS,
                actual_size=estimated_tokens,
                unit="tokens",
            )

        audience = args.get("audience", "executives")
        max_sections = args.get("max_sections", 5)

        prompt = f"""Analyze the following content and create an executive summary for {audience}.

Structure your response as JSON with these fields:
- "summary": A 2-3 paragraph executive summary
- "key_takeaways": Array of {max_sections} most important points
- "recommendations": Array of actionable recommendations (if applicable, otherwise empty array)

Content to analyze:
{text}

Respond ONLY with valid JSON, no markdown formatting."""

        result = self._call_claude(prompt, self.COMPLEX_MODEL, "executive_summary")

        # Parse JSON response
        try:
            parsed = json.loads(result["summary"])
            return {
                "summary": parsed.get("summary", ""),
                "key_takeaways": parsed.get("key_takeaways", []),
                "recommendations": parsed.get("recommendations", []),
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "model_used": result["model_used"],
                "cost_usd": result["cost_usd"],
                "status": "success",
            }
        except json.JSONDecodeError:
            # Fallback if Claude didn't return valid JSON
            return {
                "summary": result["summary"],
                "key_takeaways": [],
                "recommendations": [],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "model_used": result["model_used"],
                "cost_usd": result["cost_usd"],
                "status": "success",
            }

    def extract_bullets(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Extract key points as bullet points.

        Args:
            text: Text content to analyze (required)
            max_bullets: Maximum number of bullets (default 10)
            category: Optional category filter

        Returns:
            bullets: List of key points
            categories: Points grouped by category (if detected)
        """
        self._ensure_initialized()

        text = args.get("text")
        if not text:
            raise ValidationError("text", "Text content is required")

        # Check length
        estimated_tokens = len(text) // 4
        if estimated_tokens > self.MAX_INPUT_TOKENS:
            raise ContentTooLargeError(
                utility=self.SERVICE_NAME,
                max_size=self.MAX_INPUT_TOKENS,
                actual_size=estimated_tokens,
                unit="tokens",
            )

        max_bullets = args.get("max_bullets", 10)
        category = args.get("category")

        category_instruction = f" Focus on points related to: {category}" if category else ""

        prompt = f"""Extract the {max_bullets} most important points from the \
following content as bullet points.{category_instruction}

Structure your response as JSON with:
- "bullets": Array of strings, each a key point
- "categories": Object mapping category names to arrays of relevant bullet indices

Content:
{text}

Respond ONLY with valid JSON."""

        result = self._call_claude(prompt, self.DEFAULT_MODEL, "extract_bullets")

        try:
            parsed = json.loads(result["summary"])
            return {
                "bullets": parsed.get("bullets", []),
                "categories": parsed.get("categories", {}),
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "model_used": result["model_used"],
                "cost_usd": result["cost_usd"],
                "status": "success",
            }
        except json.JSONDecodeError:
            return {
                "bullets": [result["summary"]],
                "categories": {},
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "model_used": result["model_used"],
                "cost_usd": result["cost_usd"],
                "status": "success",
            }

    def extract_key_facts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Extract key facts, figures, and data points.

        Args:
            text: Text content to analyze (required)
            fact_types: Types of facts to extract (default: all)
                Options: "numbers", "dates", "names", "locations", "percentages"

        Returns:
            facts: List of extracted facts with type and context
            statistics: Extracted numerical data
            entities: Named entities found
        """
        self._ensure_initialized()

        text = args.get("text")
        if not text:
            raise ValidationError("text", "Text content is required")

        # Check length
        estimated_tokens = len(text) // 4
        if estimated_tokens > self.MAX_INPUT_TOKENS:
            raise ContentTooLargeError(
                utility=self.SERVICE_NAME,
                max_size=self.MAX_INPUT_TOKENS,
                actual_size=estimated_tokens,
                unit="tokens",
            )

        fact_types = args.get("fact_types", ["numbers", "dates", "names", "percentages"])

        prompt = f"""Extract key facts and data from the following content.

Focus on these fact types: {', '.join(fact_types)}

Structure your response as JSON with:
- "facts": Array of objects with "fact", "type", "context"
- "statistics": Object mapping metric names to values
- "entities": Object with "people", "organizations", "locations" arrays

Content:
{text}

Respond ONLY with valid JSON."""

        result = self._call_claude(prompt, self.DEFAULT_MODEL, "extract_key_facts")

        try:
            parsed = json.loads(result["summary"])
            return {
                "facts": parsed.get("facts", []),
                "statistics": parsed.get("statistics", {}),
                "entities": parsed.get("entities", {}),
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "model_used": result["model_used"],
                "cost_usd": result["cost_usd"],
                "status": "success",
            }
        except json.JSONDecodeError:
            return {
                "facts": [],
                "statistics": {},
                "entities": {},
                "raw_response": result["summary"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "model_used": result["model_used"],
                "cost_usd": result["cost_usd"],
                "status": "success",
            }

    def _build_summary_prompt(
        self, text: str, max_length: int, style: str, focus: str | None, language: str
    ) -> str:
        """Build the summary prompt based on parameters."""
        style_instructions = {
            "concise": (
                f"Write a concise summary in approximately {max_length} words. "
                f"Focus on the most essential information."
            ),
            "detailed": (
                f"Write a comprehensive summary covering all major points. "
                f"Target length: {max_length} words."
            ),
            "executive": (
                f"Write an executive summary suitable for senior leadership. "
                f"Be direct and actionable. Target: {max_length} words."
            ),
        }

        instruction = style_instructions.get(style, style_instructions["concise"])

        if focus:
            instruction += f" Pay particular attention to information about: {focus}"

        if language.lower() != "english":
            instruction += f" Write the summary in {language}."

        return f"""{instruction}

Content to summarize:
{text}

Summary:"""

    def _call_claude(self, prompt: str, model: str, operation: str) -> dict[str, Any]:
        """Execute Claude API call with error handling."""
        logger.info(
            f"Executing Claude {operation}",
            service=self.SERVICE_NAME,
            model=model,
            prompt_length=len(prompt),
            log_event=f"claude_{operation}_start",
        )

        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=self.MAX_OUTPUT_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # Calculate cost
            pricing = self.PRICING.get(model, self.PRICING[self.DEFAULT_MODEL])
            cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

            # Track usage
            self._track_usage(tokens_in=input_tokens, tokens_out=output_tokens, cost_usd=cost)

            # Defensive check for empty response
            if not response.content:
                raise ExecutionError(
                    "Claude returned empty response", {"model": model, "operation": operation}
                )

            summary_text = response.content[0].text

            logger.info(
                f"Claude {operation} completed",
                service=self.SERVICE_NAME,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                log_event=f"claude_{operation}_success",
            )

            return {
                "summary": summary_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model_used": model,
                "cost_usd": cost,
                "status": "success",
            }

        except anthropic.RateLimitError as e:
            logger.error(
                f"Claude rate limit hit during {operation}",
                service=self.SERVICE_NAME,
                model=model,
                log_event=f"claude_{operation}_rate_limited",
            )
            raise RateLimitError(service="anthropic") from e

        except anthropic.APIConnectionError as e:
            logger.error(
                f"Claude connection error during {operation}",
                service=self.SERVICE_NAME,
                error_type=type(e).__name__,
                log_event=f"claude_{operation}_network_error",
                exc_info=True,
            )
            raise NetworkError(service="anthropic") from e

        except anthropic.APIError as e:
            logger.error(
                f"Claude API error during {operation}",
                service=self.SERVICE_NAME,
                error_type=type(e).__name__,
                log_event=f"claude_{operation}_error",
                exc_info=True,
            )
            raise ExecutionError(
                f"Claude API error: {e!s}", {"model": model, "operation": operation}
            ) from e


# Singleton instance for registry
_summarizer_utility = None


def get_summarizer_utility() -> SummarizerUtility:
    """Get or create singleton SummarizerUtility instance."""
    global _summarizer_utility
    if _summarizer_utility is None:
        _summarizer_utility = SummarizerUtility()
    return _summarizer_utility
