"""
NEXUS AI Agent - Web Search Tool
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import aiohttp

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Web search result"""
    title: str
    url: str
    snippet: str
    score: float = 0.0


class WebSearch:
    """
    Web search tool

    Supports multiple search providers.
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = "tavily"):
        self.api_key = api_key
        self.provider = provider

    async def search(
        self,
        query: str,
        num_results: int = 5
    ) -> List[SearchResult]:
        """
        Perform web search

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of search results
        """
        if self.provider == "tavily":
            return await self._search_tavily(query, num_results)
        elif self.provider == "google":
            return await self._search_google(query, num_results)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _search_tavily(
        self,
        query: str,
        num_results: int
    ) -> List[SearchResult]:
        """Search using Tavily API"""
        if not self.api_key:
            raise ValueError("Tavily API key required")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": num_results
                }
            ) as response:
                data = await response.json()

        results = []
        for item in data.get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                score=item.get("score", 0.0)
            ))

        return results

    async def _search_google(
        self,
        query: str,
        num_results: int
    ) -> List[SearchResult]:
        """Search using Google Custom Search API"""
        # Implementation would go here
        return []

    def format_results(self, results: List[SearchResult]) -> str:
        """Format results as string"""
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r.title}\n   URL: {r.url}\n   {r.snippet}\n")
        return "\n".join(formatted)
