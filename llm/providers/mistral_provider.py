"""
NEXUS AI Agent - Mistral Provider
"""

import os
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime

from .base_provider import BaseLLMProvider, LLMResponse, GenerationConfig

from config.logging_config import get_logger


logger = get_logger(__name__)


class MistralProvider(BaseLLMProvider):
    """Mistral AI API provider"""

    PRICING = {
        "mistral-tiny": {"input": 0.00025, "output": 0.00025},
        "mistral-small": {"input": 0.001, "output": 0.003},
        "mistral-medium": {"input": 0.0027, "output": 0.0081},
        "mistral-large": {"input": 0.004, "output": 0.012},
        "mistral-large-latest": {"input": 0.004, "output": 0.012},
        "open-mistral-7b": {"input": 0.00025, "output": 0.00025},
        "open-mixtral-8x7b": {"input": 0.0007, "output": 0.0007},
        "open-mixtral-8x22b": {"input": 0.002, "output": 0.006},
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.getenv("MISTRAL_API_KEY"), **kwargs)
        self._async_client = None

    @property
    def provider_name(self) -> str:
        return "mistral"

    @property
    def supported_models(self) -> List[str]:
        return [
            "mistral-tiny",
            "mistral-small",
            "mistral-medium",
            "mistral-large",
            "mistral-large-latest",
            "open-mistral-7b",
            "open-mixtral-8x7b",
            "open-mixtral-8x22b",
        ]

    async def initialize(self) -> None:
        """Initialize Mistral client"""
        if self._initialized:
            return

        try:
            from mistralai import Mistral

            self._async_client = Mistral(api_key=self.api_key)
            self._initialized = True
            logger.info("Mistral provider initialized")

        except ImportError:
            raise ImportError("mistralai package required: pip install mistralai")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Mistral"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        try:
            response = await self._async_client.chat.complete_async(
                model=model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
            )

            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000

            content = response.choices[0].message.content

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason or "",
                latency_ms=latency,
                cost=self._calculate_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    model
                ),
                raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
            )

        except Exception as e:
            logger.error(f"Mistral generation error: {e}")
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
            stream = await self._async_client.chat.stream_async(
                model=model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
            )

            async for chunk in stream:
                if chunk.data.choices[0].delta.content:
                    yield chunk.data.choices[0].delta.content

        except Exception as e:
            logger.error(f"Mistral streaming error: {e}")
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
            response = await self._async_client.chat.complete_async(
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
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason or "",
                latency_ms=latency,
                cost=self._calculate_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    model
                ),
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error(f"Mistral tool use error: {e}")
            raise

    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate embeddings"""
        if not self._initialized:
            await self.initialize()

        model = model or "mistral-embed"

        try:
            response = await self._async_client.embeddings.create_async(
                model=model,
                inputs=[text]
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Mistral embedding error: {e}")
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
        self._async_client = None
        self._initialized = False
