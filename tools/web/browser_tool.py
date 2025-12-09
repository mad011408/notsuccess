"""NEXUS AI Agent - Browser Tool"""

import asyncio
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class BrowserAction:
    """Browser action to perform"""
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout: int = 30000


@dataclass
class BrowserResult:
    """Result of browser action"""
    success: bool
    content: str = ""
    screenshot: Optional[bytes] = None
    error: Optional[str] = None
    url: str = ""


class BrowserTool:
    """Browser automation tool using Playwright"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser = None
        self._context = None
        self._page = None

    async def start(self) -> None:
        """Start browser"""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
        except ImportError:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install")

    async def stop(self) -> None:
        """Stop browser"""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()

    async def navigate(self, url: str, wait_until: str = "networkidle") -> BrowserResult:
        """Navigate to URL"""
        if not self._page:
            await self.start()

        try:
            await self._page.goto(url, wait_until=wait_until)
            content = await self._page.content()
            return BrowserResult(success=True, content=content, url=url)
        except Exception as e:
            return BrowserResult(success=False, error=str(e), url=url)

    async def click(self, selector: str) -> BrowserResult:
        """Click element"""
        try:
            await self._page.click(selector)
            return BrowserResult(success=True, url=self._page.url)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def fill(self, selector: str, value: str) -> BrowserResult:
        """Fill input field"""
        try:
            await self._page.fill(selector, value)
            return BrowserResult(success=True, url=self._page.url)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def type_text(self, selector: str, text: str, delay: int = 50) -> BrowserResult:
        """Type text with delay"""
        try:
            await self._page.type(selector, text, delay=delay)
            return BrowserResult(success=True, url=self._page.url)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> BrowserResult:
        """Take screenshot"""
        try:
            screenshot_bytes = await self._page.screenshot(path=path, full_page=full_page)
            return BrowserResult(success=True, screenshot=screenshot_bytes, url=self._page.url)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def get_text(self, selector: str) -> BrowserResult:
        """Get text content of element"""
        try:
            element = await self._page.query_selector(selector)
            if element:
                text = await element.text_content()
                return BrowserResult(success=True, content=text or "", url=self._page.url)
            return BrowserResult(success=False, error="Element not found")
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def get_attribute(self, selector: str, attribute: str) -> BrowserResult:
        """Get attribute of element"""
        try:
            element = await self._page.query_selector(selector)
            if element:
                value = await element.get_attribute(attribute)
                return BrowserResult(success=True, content=value or "", url=self._page.url)
            return BrowserResult(success=False, error="Element not found")
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> BrowserResult:
        """Wait for element to appear"""
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return BrowserResult(success=True, url=self._page.url)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def evaluate(self, script: str) -> BrowserResult:
        """Execute JavaScript"""
        try:
            result = await self._page.evaluate(script)
            return BrowserResult(success=True, content=str(result), url=self._page.url)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def scroll(self, direction: str = "down", amount: int = 500) -> BrowserResult:
        """Scroll page"""
        try:
            if direction == "down":
                await self._page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self._page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "top":
                await self._page.evaluate("window.scrollTo(0, 0)")
            elif direction == "bottom":
                await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            return BrowserResult(success=True, url=self._page.url)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def execute_actions(self, actions: List[BrowserAction]) -> List[BrowserResult]:
        """Execute multiple actions"""
        results = []
        for action in actions:
            if action.action == "navigate":
                result = await self.navigate(action.value or "")
            elif action.action == "click":
                result = await self.click(action.selector or "")
            elif action.action == "fill":
                result = await self.fill(action.selector or "", action.value or "")
            elif action.action == "type":
                result = await self.type_text(action.selector or "", action.value or "")
            elif action.action == "screenshot":
                result = await self.screenshot()
            elif action.action == "wait":
                result = await self.wait_for_selector(action.selector or "", action.timeout)
            else:
                result = BrowserResult(success=False, error=f"Unknown action: {action.action}")
            results.append(result)
        return results

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

