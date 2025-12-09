"""NEXUS AI Agent - Content Extractor"""

import re
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


@dataclass
class ExtractedContent:
    """Extracted content from a webpage"""
    title: str = ""
    text: str = ""
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    headings: List[Dict[str, str]] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)


class ContentExtractor:
    """Extract structured content from HTML"""

    def __init__(self):
        self._remove_tags = ['script', 'style', 'nav', 'footer', 'header', 'aside']

    def extract(self, html: str, base_url: Optional[str] = None) -> ExtractedContent:
        """
        Extract content from HTML

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            ExtractedContent object
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted tags
        for tag in self._remove_tags:
            for element in soup.find_all(tag):
                element.decompose()

        content = ExtractedContent()

        # Extract title
        title_tag = soup.find('title')
        content.title = title_tag.get_text(strip=True) if title_tag else ""

        # Extract text
        content.text = self._extract_text(soup)

        # Extract links
        content.links = self._extract_links(soup, base_url)

        # Extract images
        content.images = self._extract_images(soup, base_url)

        # Extract metadata
        content.metadata = self._extract_metadata(soup)

        # Extract headings
        content.headings = self._extract_headings(soup)

        # Extract tables
        content.tables = self._extract_tables(soup)

        return content

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Try to find main content area
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if main:
            text = main.get_text(separator='\n', strip=True)
            # Clean up whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text
        return ""

    def _extract_links(self, soup: BeautifulSoup, base_url: Optional[str]) -> List[str]:
        """Extract all links"""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if base_url:
                href = urljoin(base_url, href)
            if href.startswith(('http://', 'https://')):
                links.append(href)
        return list(set(links))

    def _extract_images(self, soup: BeautifulSoup, base_url: Optional[str]) -> List[str]:
        """Extract all image URLs"""
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            if base_url:
                src = urljoin(base_url, src)
            if src.startswith(('http://', 'https://')):
                images.append(src)
        return list(set(images))

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract meta tags"""
        metadata = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property', '')
            content = meta.get('content', '')
            if name and content:
                metadata[name] = content
        return metadata

    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract headings"""
        headings = []
        for level in range(1, 7):
            for h in soup.find_all(f'h{level}'):
                headings.append({
                    'level': str(level),
                    'text': h.get_text(strip=True)
                })
        return headings

    def _extract_tables(self, soup: BeautifulSoup) -> List[List[List[str]]]:
        """Extract tables"""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = []
                for cell in tr.find_all(['td', 'th']):
                    cells.append(cell.get_text(strip=True))
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables

    def extract_article(self, html: str) -> Dict[str, Any]:
        """Extract article content specifically"""
        soup = BeautifulSoup(html, 'html.parser')

        # Try common article selectors
        article = (
            soup.find('article') or
            soup.find(class_=re.compile(r'article|post|content|entry')) or
            soup.find('main')
        )

        if not article:
            article = soup.find('body')

        return {
            'title': self._get_article_title(soup),
            'author': self._get_article_author(soup),
            'date': self._get_article_date(soup),
            'content': article.get_text(separator='\n', strip=True) if article else "",
            'summary': self._get_article_summary(soup)
        }

    def _get_article_title(self, soup: BeautifulSoup) -> str:
        """Get article title"""
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        title = soup.find('title')
        return title.get_text(strip=True) if title else ""

    def _get_article_author(self, soup: BeautifulSoup) -> str:
        """Get article author"""
        author_meta = soup.find('meta', {'name': 'author'})
        if author_meta:
            return author_meta.get('content', '')
        author_elem = soup.find(class_=re.compile(r'author|byline'))
        return author_elem.get_text(strip=True) if author_elem else ""

    def _get_article_date(self, soup: BeautifulSoup) -> str:
        """Get article date"""
        time_elem = soup.find('time')
        if time_elem:
            return time_elem.get('datetime') or time_elem.get_text(strip=True)
        date_meta = soup.find('meta', {'property': 'article:published_time'})
        return date_meta.get('content', '') if date_meta else ""

    def _get_article_summary(self, soup: BeautifulSoup) -> str:
        """Get article summary"""
        desc_meta = soup.find('meta', {'name': 'description'})
        if desc_meta:
            return desc_meta.get('content', '')
        og_desc = soup.find('meta', {'property': 'og:description'})
        return og_desc.get('content', '') if og_desc else ""

