"""NEXUS AI Agent - Google Search"""
from typing import List
import os
from .web_search import SearchResult

class GoogleSearch:
    def __init__(self, api_key: str = None, cx: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.cx = cx or os.getenv("GOOGLE_CX")

    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        import aiohttp
        url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx}&q={query}&num={num_results}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        return [SearchResult(title=i.get("title"), url=i.get("link"), snippet=i.get("snippet", "")) for i in data.get("items", [])]
