"""
Web Search utility for Stargate Lite.

Provides real-time web search capabilities via Tavily API.
Supports general search, news search, and page content extraction.

Capability keys:
- search.web: General web search
- search.news: News-focused search
- search.extract: Extract content from URL
"""

from typing import Any, ClassVar, NoReturn

import requests

from app.errors import ExecutionError, NetworkError, RateLimitError, ValidationError
from app.logging_config import get_logger
from app.utilities.base import MultiProviderUtility

logger = get_logger(__name__)


class WebSearchUtility(MultiProviderUtility):
    """
    Web search utility with Tavily as primary provider.

    Tavily is optimized for LLM applications - returns concise,
    relevant results with optional AI-generated answers.
    """

    SERVICE_NAME: ClassVar[str] = "web_search"
    credential_type: ClassVar[str] = "agent"  # Uses Aleq's API keys, not customer OAuth
    PROVIDERS: ClassVar[list[tuple[str, str]]] = [
        ("tavily", "TAVILY_API_KEY"),
    ]

    # Tavily API endpoints
    TAVILY_SEARCH_URL: ClassVar[str] = "https://api.tavily.com/search"
    TAVILY_EXTRACT_URL: ClassVar[str] = "https://api.tavily.com/extract"

    def search(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Perform web search.

        Args:
            query: Search query string (required)
            max_results: Number of results (default 5, max 20)
            search_depth: "basic" or "advanced" (default "basic")
            include_answer: Whether to include AI answer (default True)
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude

        Returns:
            results: List of search results with title, url, content, score
            answer: AI-generated answer (if include_answer=True)
            query: Original query
        """
        self._ensure_initialized()

        query = args.get("query")
        if not query:
            raise ValidationError("query", "Search query is required")

        return self._call_with_fallback(
            "search",
            query=query,
            max_results=args.get("max_results", 5),
            search_depth=args.get("search_depth", "basic"),
            include_answer=args.get("include_answer", True),
            include_domains=args.get("include_domains"),
            exclude_domains=args.get("exclude_domains"),
            topic="general",
        )

    def search_news(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Search for news articles.

        Args:
            query: Search query string (required)
            max_results: Number of results (default 5, max 20)
            days: How many days back to search (default 3)
            include_answer: Whether to include AI summary (default True)

        Returns:
            results: List of news articles with title, url, content, published_date
            answer: AI-generated summary (if include_answer=True)
            query: Original query
        """
        self._ensure_initialized()

        query = args.get("query")
        if not query:
            raise ValidationError("query", "Search query is required")

        return self._call_with_fallback(
            "search",
            query=query,
            max_results=args.get("max_results", 5),
            search_depth="advanced",
            include_answer=args.get("include_answer", True),
            topic="news",
            days=args.get("days", 3),
        )

    def extract_content(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Extract content from specific URLs.

        Args:
            urls: List of URLs to extract content from (required)

        Returns:
            results: List of extracted content with url, raw_content
            failed_results: List of URLs that failed extraction
        """
        self._ensure_initialized()

        urls = args.get("urls")
        if not urls:
            raise ValidationError("urls", "At least one URL is required")

        if isinstance(urls, str):
            urls = [urls]

        return self._call_tavily_extract(urls=urls)

    def _build_tavily_payload(
        self,
        query: str,
        max_results: int,
        search_depth: str,
        include_answer: bool,
        topic: str,
        include_domains: list[str] | None,
        exclude_domains: list[str] | None,
        days: int | None,
    ) -> dict[str, Any]:
        """Build request payload for Tavily search API."""
        api_key = self._api_keys.get("TAVILY_API_KEY")

        payload: dict[str, Any] = {
            "api_key": api_key,
            "query": query,
            "max_results": min(max_results, 20),
            "search_depth": search_depth,
            "include_answer": include_answer,
            "topic": topic,
        }

        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        if days and topic == "news":
            payload["days"] = days

        return payload

    def _handle_tavily_response(self, response: requests.Response) -> None:
        """Check response status and raise appropriate errors."""
        if response.status_code == 429:
            raise RateLimitError(service="tavily")

        if response.status_code >= 500:
            raise NetworkError(service="tavily", status_code=response.status_code)

        if response.status_code != 200:
            error_detail = response.text[:200] if response.text else "Unknown error"
            raise ExecutionError(
                f"Tavily API error: {response.status_code}",
                {"status_code": response.status_code, "detail": error_detail},
            )

    def _parse_tavily_results(
        self, data: dict[str, Any], query: str, search_depth: str
    ) -> dict[str, Any]:
        """Parse and format Tavily search response."""
        self._track_usage(cost_usd=0.01 if search_depth == "basic" else 0.02)

        logger.info(
            "Tavily search completed",
            service=self.SERVICE_NAME,
            result_count=len(data.get("results", [])),
            has_answer=bool(data.get("answer")),
            log_event="tavily_search_success",
        )

        return {
            "query": query,
            "results": [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content"),
                    "score": r.get("score"),
                    "published_date": r.get("published_date"),
                }
                for r in data.get("results", [])
            ],
            "answer": data.get("answer"),
            "response_time_ms": data.get("response_time"),
            "status": "success",
        }

    def _handle_tavily_request_error(
        self, error: Exception, query: str, log_event: str
    ) -> NoReturn:
        """Log and re-raise request errors as NetworkError."""
        if isinstance(error, requests.exceptions.Timeout):
            logger.error(
                "Tavily search timeout",
                service=self.SERVICE_NAME,
                query=query[:100],
                log_event=log_event,
            )
        else:
            logger.error(
                "Tavily search network error",
                service=self.SERVICE_NAME,
                error_type=type(error).__name__,
                log_event=log_event,
                exc_info=True,
            )
        raise NetworkError(service="tavily") from error

    def _call_tavily(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_answer: bool = True,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        topic: str = "general",
        days: int | None = None,
    ) -> dict[str, Any]:
        """Execute search via Tavily API."""
        payload = self._build_tavily_payload(
            query,
            max_results,
            search_depth,
            include_answer,
            topic,
            include_domains,
            exclude_domains,
            days,
        )

        logger.info(
            "Executing Tavily search",
            service=self.SERVICE_NAME,
            query=query[:100],
            search_depth=search_depth,
            topic=topic,
            log_event="tavily_search_start",
        )

        try:
            response = requests.post(self.TAVILY_SEARCH_URL, json=payload, timeout=30)
            self._handle_tavily_response(response)
            return self._parse_tavily_results(response.json(), query, search_depth)

        except requests.exceptions.RequestException as e:
            self._handle_tavily_request_error(e, query, "tavily_search_timeout")

    def _call_tavily_extract(self, urls: list[str]) -> dict[str, Any]:
        """Extract content from URLs via Tavily API."""
        api_key = self._api_keys.get("TAVILY_API_KEY")

        payload = {"api_key": api_key, "urls": urls}

        logger.info(
            "Executing Tavily content extraction",
            service=self.SERVICE_NAME,
            url_count=len(urls),
            log_event="tavily_extract_start",
        )

        try:
            response = requests.post(self.TAVILY_EXTRACT_URL, json=payload, timeout=60)

            if response.status_code == 429:
                raise RateLimitError(service="tavily")

            if response.status_code >= 500:
                raise NetworkError(service="tavily", status_code=response.status_code)

            if response.status_code != 200:
                error_detail = response.text[:200] if response.text else "Unknown error"
                raise ExecutionError(
                    f"Tavily extract error: {response.status_code}",
                    {"status_code": response.status_code, "detail": error_detail},
                )

            data = response.json()

            # Track usage
            self._track_usage(cost_usd=0.01 * len(urls))

            logger.info(
                "Tavily extraction completed",
                service=self.SERVICE_NAME,
                success_count=len(data.get("results", [])),
                failed_count=len(data.get("failed_results", [])),
                log_event="tavily_extract_success",
            )

            return {
                "results": [
                    {"url": r.get("url"), "raw_content": r.get("raw_content")}
                    for r in data.get("results", [])
                ],
                "failed_results": data.get("failed_results", []),
                "status": "success",
            }

        except requests.exceptions.Timeout as e:
            logger.error(
                "Tavily extraction timeout",
                service=self.SERVICE_NAME,
                url_count=len(urls),
                log_event="tavily_extract_timeout",
            )
            raise NetworkError(service="tavily") from e
        except requests.exceptions.RequestException as e:
            logger.error(
                "Tavily extraction network error",
                service=self.SERVICE_NAME,
                error_type=type(e).__name__,
                log_event="tavily_extract_error",
                exc_info=True,
            )
            raise NetworkError(service="tavily") from e


# Singleton instance for registry
_web_search_utility = None


def get_web_search_utility() -> WebSearchUtility:
    """Get or create singleton WebSearchUtility instance."""
    global _web_search_utility
    if _web_search_utility is None:
        _web_search_utility = WebSearchUtility()
    return _web_search_utility
