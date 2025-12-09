"""
NEXUS AI Agent - Bytez Provider
OpenAI-compatible API for Bytez models (GPT models)
"""

import aiohttp
import asyncio
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime

from .base_provider import BaseLLMProvider, LLMResponse, GenerationConfig

from config.logging_config import get_logger
from config.constants import (
    BYTEZ_API_KEY,
    BYTEZ_API_BASE_URL,
    BYTEZ_MODELS,
    MODEL_PRICING
)


logger = get_logger(__name__)


class BytezProvider(BaseLLMProvider):
    """
    Bytez API Provider
    OpenAI-compatible endpoint for GPT models

    Available Models:
    - openai/gpt-4.1
    - openai/gpt-4o
    - openai/gpt-5.1
    - openai/gpt-5
    """

    PRICING = {
        "openai/gpt-4.1": {"input": 0.01, "output": 0.03},
        "openai/gpt-4o": {"input": 0.005, "output": 0.015},
        "openai/gpt-5.1": {"input": 0.02, "output": 0.06},
        "openai/gpt-5": {"input": 0.02, "output": 0.06},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(api_key or BYTEZ_API_KEY, **kwargs)
        self.base_url = base_url or BYTEZ_API_BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None
        self._response_counter = 0

    @property
    def provider_name(self) -> str:
        return "bytez"

    @property
    def supported_models(self) -> List[str]:
        return BYTEZ_MODELS

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def initialize(self) -> None:
        """Initialize HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=300, connect=30)
            self._session = aiohttp.ClientSession(
                headers=self._get_headers(),
                timeout=timeout
            )
        self._initialized = True
        logger.info(f"Bytez Provider initialized with base URL: {self.base_url}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Bytez API (OpenAI-compatible)"""
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

        # Bytez API - cap max_tokens at 4096
        max_tokens = min(config.max_tokens, 4096)

        # Build request payload (OpenAI format)
        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": False,
        }

        # Add system message to the beginning of messages
        if system_message:
            payload["messages"] = [{"role": "system", "content": system_message}] + chat_messages
            logger.info(f"[BYTEZ #{self._response_counter}] System prompt attached (length: {len(system_message)} chars)")
        else:
            logger.warning(f"[BYTEZ #{self._response_counter}] NO SYSTEM PROMPT!")

        if config.stop_sequences:
            payload["stop"] = config.stop_sequences

        try:
            endpoint = f"{self.base_url}/chat/completions"

            async with self._session.post(endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Bytez API error {response.status}: {error_text}")
                    raise Exception(f"Bytez API error {response.status}: {error_text}")

                data = await response.json()

            # Parse response
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens, model)

            return LLMResponse(
                content=content,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost=cost,
                latency=(datetime.utcnow() - start_time).total_seconds(),
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
                raw_response=data
            )

        except Exception as e:
            logger.error(f"Bytez generate error: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from Bytez API"""
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

        # Bytez API - cap max_tokens at 4096
        max_tokens = min(config.max_tokens, 4096)

        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": config.temperature,
            "stream": True,
        }

        # Add system message
        if system_message:
            payload["messages"] = [{"role": "system", "content": system_message}] + chat_messages
            logger.info(f"[BYTEZ STREAM #{self._response_counter}] System prompt attached (length: {len(system_message)} chars)")
        else:
            logger.warning(f"[BYTEZ STREAM #{self._response_counter}] NO SYSTEM PROMPT!")

        try:
            endpoint = f"{self.base_url}/chat/completions"

            timeout = aiohttp.ClientTimeout(total=1800, sock_read=300)

            async with aiohttp.ClientSession(
                headers=self._get_headers(),
                timeout=timeout
            ) as session:
                async with session.post(endpoint, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Bytez API error {response.status}: {error_text}")

                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content'] is not None:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"Bytez stream error: {e}")
            raise

    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: List[Dict[str, Any]],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate with tool use (OpenAI function calling format)"""
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

        # Bytez API - cap max_tokens at 4096
        max_tokens = min(config.max_tokens, 4096)

        # Convert tools to OpenAI format
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", tool.get("parameters", {}))
                }
            })

        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": config.temperature,
            "tools": openai_tools,
        }

        # Add system message
        if system_message:
            payload["messages"] = [{"role": "system", "content": system_message}] + chat_messages
            logger.info(f"[BYTEZ TOOLS #{self._response_counter}] System prompt attached (length: {len(system_message)} chars)")
        else:
            logger.warning(f"[BYTEZ TOOLS #{self._response_counter}] NO SYSTEM PROMPT!")

        try:
            endpoint = f"{self.base_url}/chat/completions"

            async with self._session.post(endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Bytez API error {response.status}: {error_text}")

                data = await response.json()

            # Parse response
            choice = data["choices"][0]
            message = choice["message"]
            content = message.get("content", "")

            # Check for tool calls
            tool_calls = []
            if "tool_calls" in message:
                for tc in message["tool_calls"]:
                    tool_calls.append({
                        "id": tc.get("id", ""),
                        "type": "function",
                        "name": tc["function"]["name"],
                        "input": json.loads(tc["function"]["arguments"])
                    })

            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            cost = self._calculate_cost(input_tokens, output_tokens, model)

            return LLMResponse(
                content=content,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost=cost,
                latency=(datetime.utcnow() - start_time).total_seconds(),
                finish_reason=choice.get("finish_reason", "stop"),
                tool_calls=tool_calls if tool_calls else None,
                raw_response=data
            )

        except Exception as e:
            logger.error(f"Bytez generate_with_tools error: {e}")
            raise

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for API call"""
        pricing = self.PRICING.get(model, {"input": 0.01, "output": 0.03})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
        self._initialized = False
        logger.info("Bytez Provider closed")
