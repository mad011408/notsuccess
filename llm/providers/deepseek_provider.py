"""
NEXUS AI Agent - DeepSeek Provider
"""

import os
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime

from .base_provider import BaseLLMProvider, LLMResponse, GenerationConfig

from config.logging_config import get_logger


logger = get_logger(__name__)


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek API provider"""

    PRICING = {
        "deepseek-chat": {"input": 0.00014, "output": 0.00028},
        "deepseek-coder": {"input": 0.00014, "output": 0.00028},
        "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.getenv("DEEPSEEK_API_KEY"), **kwargs)
        self._async_client = None
        self._base_url = "https://api.deepseek.com"

    @property
    def provider_name(self) -> str:
        return "deepseek"

    @property
    def supported_models(self) -> List[str]:
        return [
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-reasoner",
        ]

    async def initialize(self) -> None:
        """Initialize DeepSeek client (OpenAI compatible)"""
        if self._initialized:
            return

        try:
            from openai import AsyncOpenAI

            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self._base_url
            )
            self._initialized = True
            logger.info("DeepSeek provider initialized")

        except ImportError:
            raise ImportError("openai package required: pip install openai")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from DeepSeek"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        try:
            response = await self._async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop_sequences,
            )

            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=model,
                provider=self.provider_name,
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason or "",
                latency_ms=latency,
                cost=self._calculate_cost(
                    response.usage.prompt_tokens if response.usage else 0,
                    response.usage.completion_tokens if response.usage else 0,
                    model
                ),
                raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
            )

        except Exception as e:
            logger.error(f"DeepSeek generation error: {e}")
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

        try:
            stream = await self._async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            raise

    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: List[Dict[str, Any]],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate with function calling"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        try:
            response = await self._async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                tools=tools,
                tool_choice=kwargs.get("tool_choice", "auto"),
            )

            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000

            content = response.choices[0].message.content or ""
            tool_calls = None

            if response.choices[0].message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in response.choices[0].message.tool_calls
                ]

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason or "",
                latency_ms=latency,
                cost=self._calculate_cost(
                    response.usage.prompt_tokens if response.usage else 0,
                    response.usage.completion_tokens if response.usage else 0,
                    model
                ),
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error(f"DeepSeek tool use error: {e}")
            raise

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for API call"""
        pricing = self.PRICING.get(model, {"input": 0.0, "output": 0.0})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    async def close(self) -> None:
        """Cleanup"""
        if self._async_client:
            await self._async_client.close()
        self._async_client = None
        self._initialized = False
