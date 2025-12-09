"""
NEXUS AI Agent - OpenRouter Provider
OpenAI-compatible API for OpenRouter models
"""

import aiohttp
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime

from .base_provider import BaseLLMProvider, LLMResponse, GenerationConfig

from config.logging_config import get_logger
from config.constants import (
    OPENROUTER_API_KEY,
    OPENROUTER_API_BASE_URL,
    OPENROUTER_MODELS
)


logger = get_logger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter API Provider
    OpenAI-compatible endpoint for various models

    Available Models:
    - deepseek/deepseek-v3.2-speciale
    - moonshotai/kimi-k2:free
    """

    PRICING = {
        "deepseek/deepseek-v3.2-speciale": {"input": 0.001, "output": 0.002},
        "moonshotai/kimi-k2:free": {"input": 0.0, "output": 0.0},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(api_key or OPENROUTER_API_KEY, **kwargs)
        self.base_url = base_url or OPENROUTER_API_BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None
        self._response_counter = 0

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def supported_models(self) -> List[str]:
        return OPENROUTER_MODELS

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nexus-ai-agent.local",
            "X-Title": "NEXUS AI Agent",
            # Allow data training for free models
            "X-Allow-Data-Training": "true",
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
        logger.info(f"OpenRouter Provider initialized with base URL: {self.base_url}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenRouter API"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        # Extract system message
        system_message = ""
        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "") or ""
            if role == "system":
                system_message = content
            else:
                chat_messages.append({
                    "role": role,
                    "content": content
                })

        # Increment response counter
        self._response_counter += 1

        # OpenRouter - cap max_tokens at 4096
        max_tokens = min(config.max_tokens, 4096)

        # Build request payload
        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": False,
            # OpenRouter specific - allow free models
            "provider": {
                "allow_fallbacks": True,
                "data_collection": "allow"
            }
        }

        # Add system message
        if system_message:
            payload["messages"] = [{"role": "system", "content": system_message}] + chat_messages
            logger.info(f"[OPENROUTER #{self._response_counter}] System prompt attached (length: {len(system_message)} chars)")
        else:
            logger.warning(f"[OPENROUTER #{self._response_counter}] NO SYSTEM PROMPT!")

        if config.stop_sequences:
            payload["stop"] = config.stop_sequences

        try:
            endpoint = f"{self.base_url}/chat/completions"

            async with self._session.post(endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error {response.status}: {error_text}")
                    raise Exception(f"OpenRouter API error {response.status}: {error_text}")

                data = await response.json()

            # Parse response
            content = data["choices"][0]["message"]["content"] or ""
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
            logger.error(f"OpenRouter generate error: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenRouter API"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()

        # Extract system message
        system_message = ""
        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "") or ""
            if role == "system":
                system_message = content
            else:
                chat_messages.append({
                    "role": role,
                    "content": content
                })

        # Increment response counter
        self._response_counter += 1

        # OpenRouter - cap max_tokens at 4096
        max_tokens = min(config.max_tokens, 4096)

        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": config.temperature,
            "stream": True,
            # OpenRouter specific - allow free models
            "provider": {
                "allow_fallbacks": True,
                "data_collection": "allow"
            }
        }

        # Add system message
        if system_message:
            payload["messages"] = [{"role": "system", "content": system_message}] + chat_messages
            logger.info(f"[OPENROUTER STREAM #{self._response_counter}] System prompt attached (length: {len(system_message)} chars)")
        else:
            logger.warning(f"[OPENROUTER STREAM #{self._response_counter}] NO SYSTEM PROMPT!")

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
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")

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
            logger.error(f"OpenRouter stream error: {e}")
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
            content = msg.get("content", "") or ""
            if role == "system":
                system_message = content
            else:
                chat_messages.append({
                    "role": role,
                    "content": content
                })

        # Increment response counter
        self._response_counter += 1

        # OpenRouter - cap max_tokens at 4096
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
            # OpenRouter specific - allow free models
            "provider": {
                "allow_fallbacks": True,
                "data_collection": "allow"
            }
        }

        # Add system message
        if system_message:
            payload["messages"] = [{"role": "system", "content": system_message}] + chat_messages
            logger.info(f"[OPENROUTER TOOLS #{self._response_counter}] System prompt attached (length: {len(system_message)} chars)")
        else:
            logger.warning(f"[OPENROUTER TOOLS #{self._response_counter}] NO SYSTEM PROMPT!")

        try:
            endpoint = f"{self.base_url}/chat/completions"

            async with self._session.post(endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error {response.status}: {error_text}")

                data = await response.json()

            # Parse response
            choice = data["choices"][0]
            message = choice["message"]
            content = message.get("content", "") or ""

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
            logger.error(f"OpenRouter generate_with_tools error: {e}")
            raise

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for API call"""
        pricing = self.PRICING.get(model, {"input": 0.001, "output": 0.002})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
        self._initialized = False
        logger.info("OpenRouter Provider closed")
