"""
NEXUS AI Agent - Groq Provider (Fast Inference)
"""

import os
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime

from .base_provider import BaseLLMProvider, LLMResponse, GenerationConfig

from config.logging_config import get_logger


logger = get_logger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq API provider for fast inference"""

    PRICING = {
        "llama-3.1-405b-reasoning": {"input": 0.0, "output": 0.0},
        "llama-3.1-70b-versatile": {"input": 0.0, "output": 0.0},
        "llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},
        "llama3-groq-70b-8192-tool-use-preview": {"input": 0.0, "output": 0.0},
        "llama3-groq-8b-8192-tool-use-preview": {"input": 0.0, "output": 0.0},
        "mixtral-8x7b-32768": {"input": 0.0, "output": 0.0},
        "gemma-7b-it": {"input": 0.0, "output": 0.0},
        "gemma2-9b-it": {"input": 0.0, "output": 0.0},
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.getenv("GROQ_API_KEY"), **kwargs)
        self._async_client = None

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def supported_models(self) -> List[str]:
        return list(self.PRICING.keys())

    async def initialize(self) -> None:
        """Initialize Groq client"""
        if self._initialized:
            return

        try:
            from groq import AsyncGroq

            self._async_client = AsyncGroq(api_key=self.api_key)
            self._initialized = True
            logger.info("Groq provider initialized")

        except ImportError:
            raise ImportError("groq package required: pip install groq")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Groq"""
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
                cost=0.0,  # Groq is currently free
                raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
            )

        except Exception as e:
            logger.error(f"Groq generation error: {e}")
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
            logger.error(f"Groq streaming error: {e}")
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

        # Use tool-use specific models
        if "tool-use" not in model:
            model = "llama3-groq-70b-8192-tool-use-preview"

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
                cost=0.0,
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error(f"Groq tool use error: {e}")
            raise

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Groq is currently free"""
        return 0.0

    async def close(self) -> None:
        """Cleanup"""
        if self._async_client:
            await self._async_client.close()
        self._async_client = None
        self._initialized = False
