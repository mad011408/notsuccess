"""
NEXUS AI Agent - Anthropic Provider
TryBons AI Integration - Claude Models Only
"""

import aiohttp
import asyncio
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime

from .base_provider import BaseLLMProvider, LLMResponse, GenerationConfig

from config.logging_config import get_logger
from config.constants import API_KEY, API_BASE_URL, AVAILABLE_MODELS


logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic API provider for TryBons AI
    Supports: claude-opus-4-1-20250805, claude-opus-4-5, claude-opus-4-5-20251101
    """

    # TryBons AI Configuration
    DEFAULT_API_KEY = API_KEY
    DEFAULT_BASE_URL = API_BASE_URL

    PRICING = {
        "claude-opus-4-1-20250805": {"input": 0.015, "output": 0.075},
        "claude-opus-4-5": {"input": 0.015, "output": 0.075},
        "claude-opus-4-5-20251101": {"input": 0.015, "output": 0.075},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(api_key or self.DEFAULT_API_KEY, **kwargs)
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None
        # Response counter for enforcement tracking
        self._response_counter: int = 0

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def supported_models(self) -> List[str]:
        return AVAILABLE_MODELS.copy()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key
        }

    async def initialize(self) -> None:
        """Initialize HTTP session"""
        if self._initialized:
            return

        self._session = aiohttp.ClientSession(
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=1600)
        )
        self._initialized = True
        logger.info(f"Anthropic provider initialized with base URL: {self.base_url}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from TryBons AI"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        # Extract system message
        system_message = ""
        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "") or ""  # Handle None content
            if role == "system":
                system_message = content
            else:
                chat_messages.append({
                    "role": role,
                    "content": content
                })

        # Increment response counter
        self._response_counter += 1

        # Build request payload
        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
        }

        # DIRECT pass - system prompt goes straight to model EVERY TIME
        if system_message:
            payload["system"] = system_message
            logger.info(f"[REQUEST #{self._response_counter}] System prompt attached (length: {len(system_message)} chars)")
        else:
            logger.warning(f"[REQUEST #{self._response_counter}] NO SYSTEM PROMPT - this should not happen!")

        if config.stop_sequences:
            payload["stop_sequences"] = config.stop_sequences

        try:
            endpoint = f"{self.base_url}/v1/messages"

            async with self._session.post(endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    raise Exception(f"API error {response.status}: {error_text}")

                data = await response.json()

            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000

            # Extract content
            content = ""
            if "content" in data:
                for block in data["content"]:
                    if isinstance(block, dict) and block.get("type") == "text":
                        content += block.get("text", "")
                    elif isinstance(block, str):
                        content += block

            # Extract usage
            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                finish_reason=data.get("stop_reason", ""),
                latency_ms=latency,
                cost=self._calculate_cost(input_tokens, output_tokens, model),
                raw_response=data,
            )

        except Exception as e:
            logger.error(f"TryBons AI generation error: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()

        # Extract system message
        system_message = ""
        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "") or ""  # Handle None content
            if role == "system":
                system_message = content
            else:
                chat_messages.append({
                    "role": role,
                    "content": content
                })

        # Increment response counter
        self._response_counter += 1

        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": True,
        }

        # DIRECT pass - system prompt goes straight to model EVERY TIME
        if system_message:
            payload["system"] = system_message
            logger.info(f"[STREAM #{self._response_counter}] System prompt attached (length: {len(system_message)} chars)")
        else:
            logger.warning(f"[STREAM #{self._response_counter}] NO SYSTEM PROMPT - this should not happen!")

        try:
            endpoint = f"{self.base_url}/v1/messages"

            # Create new session with longer timeout for streaming
            timeout = aiohttp.ClientTimeout(total=1800, sock_read=300)

            async with aiohttp.ClientSession(
                headers=self._get_headers(),
                timeout=timeout
            ) as session:
                async with session.post(endpoint, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API error {response.status}: {error_text}")

                    buffer = ""
                    async for chunk in response.content.iter_any():
                        if chunk:
                            buffer += chunk.decode("utf-8", errors="ignore")

                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                line = line.strip()

                                if not line:
                                    continue

                                # Handle event: lines (SSE format)
                                if line.startswith("event:"):
                                    continue

                                if line.startswith("data: "):
                                    data_str = line[6:]

                                    if data_str == "[DONE]":
                                        return

                                    try:
                                        data = json.loads(data_str)

                                        # Handle different event types
                                        event_type = data.get("type", "")

                                        if event_type == "content_block_delta":
                                            delta = data.get("delta", {})
                                            if delta.get("type") == "text_delta":
                                                text = delta.get("text", "")
                                                if text:
                                                    yield text

                                        elif event_type == "message_stop":
                                            return

                                        elif event_type == "error":
                                            error_msg = data.get("error", {}).get("message", "Unknown error")
                                            logger.error(f"Stream error: {error_msg}")
                                            raise Exception(error_msg)

                                    except json.JSONDecodeError:
                                        continue

                    # Process remaining buffer
                    if buffer.strip():
                        if buffer.strip().startswith("data: "):
                            data_str = buffer.strip()[6:]
                            if data_str and data_str != "[DONE]":
                                try:
                                    data = json.loads(data_str)
                                    if data.get("type") == "content_block_delta":
                                        delta = data.get("delta", {})
                                        if delta.get("type") == "text_delta":
                                            text = delta.get("text", "")
                                            if text:
                                                yield text
                                except json.JSONDecodeError:
                                    pass

        except aiohttp.ClientError as e:
            logger.error(f"TryBons AI connection error: {e}")
            raise Exception(f"Connection error: {e}")
        except asyncio.TimeoutError:
            logger.error("TryBons AI streaming timeout")
            raise Exception("Request timed out")
        except Exception as e:
            logger.error(f"TryBons AI streaming error: {e}")
            raise

    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: List[Dict[str, Any]],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate with tool use"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        # Extract system message
        system_message = ""
        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "") or ""  # Handle None content
            if role == "system":
                system_message = content
            else:
                chat_messages.append({
                    "role": role,
                    "content": content
                })

        # Convert tools to Anthropic format
        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append({
                "name": tool.get("name") or tool.get("function", {}).get("name"),
                "description": tool.get("description") or tool.get("function", {}).get("description"),
                "input_schema": tool.get("parameters") or tool.get("function", {}).get("parameters", {})
            })

        # Increment response counter
        self._response_counter += 1

        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "tools": anthropic_tools,
        }

        # DIRECT pass - system prompt goes straight to model EVERY TIME
        if system_message:
            payload["system"] = system_message
            logger.info(f"[TOOLS #{self._response_counter}] System prompt attached (length: {len(system_message)} chars)")
        else:
            logger.warning(f"[TOOLS #{self._response_counter}] NO SYSTEM PROMPT - this should not happen!")

        try:
            endpoint = f"{self.base_url}/v1/messages"

            async with self._session.post(endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")

                data = await response.json()

            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000

            content = ""
            tool_calls = []

            for block in data.get("content", []):
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        content += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        tool_calls.append({
                            "id": block.get("id"),
                            "type": "function",
                            "function": {
                                "name": block.get("name"),
                                "arguments": block.get("input", {})
                            }
                        })

            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                finish_reason=data.get("stop_reason", ""),
                latency_ms=latency,
                cost=self._calculate_cost(input_tokens, output_tokens, model),
                raw_response=data,
                tool_calls=tool_calls if tool_calls else None,
            )

        except Exception as e:
            logger.error(f"TryBons AI tool use error: {e}")
            raise

    def count_tokens(self, text: str, model: str) -> int:
        """Estimate token count"""
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for API call"""
        pricing = self.PRICING.get(model, {"input": 0.015, "output": 0.075})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    async def close(self) -> None:
        """Cleanup"""
        if self._session:
            await self._session.close()
        self._session = None
        self._initialized = False


# Alias for compatibility
TryBonsProvider = AnthropicProvider
ClaudeProvider = AnthropicProvider
