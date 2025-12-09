"""NEXUS AI Agent - Web Scraper Tool"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
import aiohttp
from bs4 import BeautifulSoup

@dataclass
class ScrapedContent:
    url: str
    title: str
    text: str
    html: str
    metadata: Dict[str, Any]

class WebScraper:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def scrape(self, url: str, extract_text: bool = True) -> ScrapedContent:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else ""
        text = soup.get_text(separator=" ", strip=True) if extract_text else ""

        return ScrapedContent(url=url, title=title, text=text[:10000], html=html, metadata={"status": response.status})

    async def extract_links(self, url: str) -> list:
        content = await self.scrape(url, extract_text=False)
        soup = BeautifulSoup(content.html, "html.parser")
        return [a.get("href") for a in soup.find_all("a", href=True)]
