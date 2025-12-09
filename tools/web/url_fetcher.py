"""NEXUS AI Agent - URL Fetcher"""
import aiohttp
from typing import Optional, Dict

class URLFetcher:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {"User-Agent": "NEXUS-Agent/1.0"}

    async def fetch(self, url: str, headers: Optional[Dict] = None) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers or self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                return await response.text()

    async def fetch_json(self, url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                return await response.json()
