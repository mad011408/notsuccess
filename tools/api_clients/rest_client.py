"""NEXUS AI Agent - REST Client"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class APIResponse:
    """API response"""
    status: int
    data: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    elapsed: float = 0.0


@dataclass
class APIConfig:
    """API configuration"""
    base_url: str = ""
    timeout: int = 30
    headers: Dict[str, str] = field(default_factory=dict)
    auth: Optional[tuple] = None
    verify_ssl: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0


class RESTClient:
    """REST API client"""

    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self.config.headers
            )
        return self._session

    async def close(self) -> None:
        """Close session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def request(
        self,
        method: HTTPMethod,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> APIResponse:
        """
        Make HTTP request

        Args:
            method: HTTP method
            url: URL or path
            params: Query parameters
            data: Form data
            json: JSON body
            headers: Additional headers

        Returns:
            APIResponse
        """
        import time
        start_time = time.time()

        # Build full URL
        full_url = url if url.startswith('http') else f"{self.config.base_url}{url}"

        session = await self._get_session()

        # Merge headers
        request_headers = {**self.config.headers, **(headers or {})}

        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                async with session.request(
                    method.value,
                    full_url,
                    params=params,
                    data=data,
                    json=json,
                    headers=request_headers,
                    ssl=self.config.verify_ssl,
                    **kwargs
                ) as response:
                    # Parse response
                    content_type = response.headers.get('Content-Type', '')

                    if 'application/json' in content_type:
                        response_data = await response.json()
                    else:
                        response_data = await response.text()

                    return APIResponse(
                        status=response.status,
                        data=response_data,
                        headers=dict(response.headers),
                        elapsed=time.time() - start_time
                    )

            except asyncio.TimeoutError:
                last_error = "Request timed out"
            except aiohttp.ClientError as e:
                last_error = str(e)

            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        return APIResponse(
            status=0,
            error=last_error,
            elapsed=time.time() - start_time
        )

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """GET request"""
        return await self.request(HTTPMethod.GET, url, params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """POST request"""
        return await self.request(HTTPMethod.POST, url, data=data, json=json, **kwargs)

    async def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """PUT request"""
        return await self.request(HTTPMethod.PUT, url, data=data, json=json, **kwargs)

    async def patch(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """PATCH request"""
        return await self.request(HTTPMethod.PATCH, url, data=data, json=json, **kwargs)

    async def delete(self, url: str, **kwargs) -> APIResponse:
        """DELETE request"""
        return await self.request(HTTPMethod.DELETE, url, **kwargs)

    async def head(self, url: str, **kwargs) -> APIResponse:
        """HEAD request"""
        return await self.request(HTTPMethod.HEAD, url, **kwargs)

    async def download(
        self,
        url: str,
        destination: str,
        chunk_size: int = 8192
    ) -> APIResponse:
        """Download file"""
        import time
        start_time = time.time()

        full_url = url if url.startswith('http') else f"{self.config.base_url}{url}"
        session = await self._get_session()

        try:
            async with session.get(full_url) as response:
                with open(destination, 'wb') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        f.write(chunk)

                return APIResponse(
                    status=response.status,
                    data={"path": destination},
                    headers=dict(response.headers),
                    elapsed=time.time() - start_time
                )

        except Exception as e:
            return APIResponse(
                status=0,
                error=str(e),
                elapsed=time.time() - start_time
            )

    async def upload(
        self,
        url: str,
        file_path: str,
        field_name: str = "file",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """Upload file"""
        import time
        start_time = time.time()

        full_url = url if url.startswith('http') else f"{self.config.base_url}{url}"
        session = await self._get_session()

        try:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field(field_name, f)

                if additional_data:
                    for key, value in additional_data.items():
                        data.add_field(key, str(value))

                async with session.post(full_url, data=data) as response:
                    response_data = await response.json()

                    return APIResponse(
                        status=response.status,
                        data=response_data,
                        headers=dict(response.headers),
                        elapsed=time.time() - start_time
                    )

        except Exception as e:
            return APIResponse(
                status=0,
                error=str(e),
                elapsed=time.time() - start_time
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

