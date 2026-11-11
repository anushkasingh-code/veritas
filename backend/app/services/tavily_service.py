"""
Web Search Service wrapper for Tavily API.
Provides normalized search results for agent RAG retrieval and evidence lookup.
"""

from abc import ABC, abstractmethod
import logging
from typing import List, Optional
from urllib.parse import urlparse

from tavily import TavilyClient

from app.core.config import settings
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class BaseSearchService(ABC):
    """
    Abstract Base Class for web search providers.
    Enables adding alternative search providers behind a common interface.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = False,
        include_raw_content: bool = True,
    ) -> List[SearchResult]:
        """
        Executes a web search query and returns normalized SearchResult items.
        """
        pass


class TavilyService(BaseSearchService):
    """
    Singleton Tavily Search API client wrapper.
    """

    _instance: Optional["TavilyService"] = None
    _client: Optional[TavilyClient] = None

    def __new__(cls) -> "TavilyService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance

    def _get_client(self) -> TavilyClient:
        """
        Lazily initializes and validates the TavilyClient instance.
        """
        if self._client is None:
            api_key = settings.tavily_api_key_str
            if not api_key:
                logger.error("Tavily API key is missing in environment configuration.")
                raise ValueError(
                    "TAVILY_API_KEY is not set in environment variables or .env configuration."
                )

            logger.info("Initializing TavilyClient instance...")
            self._client = TavilyClient(api_key=api_key)

        return self._client

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extracts network location domain from a target URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = False,
        include_raw_content: bool = True,
    ) -> List[SearchResult]:
        """
        Executes a web search query via Tavily API and returns normalized SearchResult objects.

        Args:
            query: The web search query string.
            max_results: Maximum number of search results to return (default: 5).
            include_answer: Whether to request an LLM answer summary from Tavily.
            include_raw_content: Whether to request full raw HTML/text content.

        Returns:
            List[SearchResult]: Strongly typed Pydantic search results.
        """
        if not query or not query.strip():
            raise ValueError("Search query must be a non-empty string.")

        if max_results < 1:
            raise ValueError("max_results must be a positive integer greater than 0.")

        clean_query = query.strip()
        client = self._get_client()

        logger.info(f"Executing Tavily web search: query='{clean_query}', max_results={max_results}")

        try:
            response = client.search(
                query=clean_query,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
            )
        except Exception as e:
            logger.error(f"Tavily API request failed for query '{clean_query}': {e}", exc_info=True)
            raise RuntimeError(f"Tavily web search failed for query '{clean_query}': {str(e)}") from e

        results: List[SearchResult] = []
        raw_results = response.get("results", [])

        for item in raw_results:
            url = item.get("url", "")
            raw = item.get("raw_content") if include_raw_content else None
            content = raw or item.get("content", "")

            search_result = SearchResult(
                title=item.get("title", "Untitled Document"),
                url=url,
                content=content,
                score=float(item.get("score", 0.0)),
                published_date=item.get("published_date"),
                domain=self._extract_domain(url),
                provider="tavily",
            )
            results.append(search_result)

        logger.info(f"Successfully retrieved {len(results)} normalized SearchResult items from Tavily.")
        return results


# Singleton instance export
tavily_service = TavilyService()


def get_tavily_service() -> TavilyService:
    """
    Returns the singleton TavilyService instance.
    """
    return tavily_service
