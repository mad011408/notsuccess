"""NEXUS AI Agent - Tavily Search"""
from typing import List
import os
from .web_search import SearchResult

class TavilySearch:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

    async def search(self, query: str, num_results: int = 5, search_depth: str = "basic") -> List[SearchResult]:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.tavily.com/search", json={"api_key": self.api_key, "query": query, "max_results": num_results, "search_depth": search_depth}) as response:
                data = await response.json()
        return [SearchResult(title=r.get("title"), url=r.get("url"), snippet=r.get("content", ""), score=r.get("score", 0)) for r in data.get("results", [])]
