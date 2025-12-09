"""
NEXUS AI Agent - OpenAI Provider
"""

import os
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
import asyncio

from .base_provider import BaseLLMProvider, LLMResponse, GenerationConfig

from config.logging_config import get_logger


logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider (GPT-4, GPT-4o, o1, etc.)"""

    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "o1": {"input": 0.015, "output": 0.06},
        "o1-mini": {"input": 0.003, "output": 0.012},
        "o1-preview": {"input": 0.015, "output": 0.06},
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"), **kwargs)
        self._async_client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "o1",
            "o1-mini",
            "o1-preview",
        ]

    async def initialize(self) -> None:
        """Initialize OpenAI client"""
        if self._initialized:
            return

        try:
            from openai import AsyncOpenAI

            self._async_client = AsyncOpenAI(api_key=self.api_key)
            self._initialized = True
            logger.info("OpenAI provider initialized")

        except ImportError:
            raise ImportError("openai package required: pip install openai")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from OpenAI"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        # Handle o1 models (no system message, no streaming)
        is_o1 = model.startswith("o1")
        if is_o1:
            messages = self._convert_o1_messages(messages)

        try:
            request_params = {
                "model": model,
                "messages": messages,
                "max_tokens": config.max_tokens,
            }

            # o1 models don't support these parameters
            if not is_o1:
                request_params.update({
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "frequency_penalty": config.frequency_penalty,
                    "presence_penalty": config.presence_penalty,
                })

                if config.stop_sequences:
                    request_params["stop"] = config.stop_sequences

                if config.json_mode:
                    request_params["response_format"] = {"type": "json_object"}

                if config.seed:
                    request_params["seed"] = config.seed

            response = await self._async_client.chat.completions.create(**request_params)

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
                raw_response=response.model_dump(),
                function_call=response.choices[0].message.function_call.model_dump()
                    if response.choices[0].message.function_call else None,
                tool_calls=[tc.model_dump() for tc in response.choices[0].message.tool_calls]
                    if response.choices[0].message.tool_calls else None
            )

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
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

        # o1 models don't support streaming
        if model.startswith("o1"):
            response = await self.generate(messages, model, config, **kwargs)
            yield response.content
            return

        try:
            request_params = {
                "model": model,
                "messages": messages,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "stream": True,
            }

            if config.stop_sequences:
                request_params["stop"] = config.stop_sequences

            stream = await self._async_client.chat.completions.create(**request_params)

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise

    async def generate_with_functions(
        self,
        messages: List[Dict[str, str]],
        model: str,
        functions: List[Dict[str, Any]],
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
                functions=functions,
                function_call=kwargs.get("function_call", "auto"),
                max_tokens=config.max_tokens,
                temperature=config.temperature,
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
                raw_response=response.model_dump(),
                function_call=response.choices[0].message.function_call.model_dump()
                    if response.choices[0].message.function_call else None,
            )

        except Exception as e:
            logger.error(f"OpenAI function calling error: {e}")
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

        try:
            response = await self._async_client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice=kwargs.get("tool_choice", "auto"),
                max_tokens=config.max_tokens,
                temperature=config.temperature,
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
                raw_response=response.model_dump(),
                tool_calls=[tc.model_dump() for tc in response.choices[0].message.tool_calls]
                    if response.choices[0].message.tool_calls else None,
            )

        except Exception as e:
            logger.error(f"OpenAI tool use error: {e}")
            raise

    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate embeddings"""
        if not self._initialized:
            await self.initialize()

        model = model or "text-embedding-3-small"

        try:
            response = await self._async_client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens using tiktoken"""
        try:
            import tiktoken

            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")

            return len(encoding.encode(text))

        except ImportError:
            # Fallback to estimation
            return len(text) // 4

    def _convert_o1_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert messages for o1 models (no system message)"""
        converted = []
        system_content = ""

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                converted.append(msg)

        # Prepend system content to first user message
        if system_content and converted:
            if converted[0]["role"] == "user":
                converted[0]["content"] = f"{system_content}\n\n{converted[0]['content']}"

        return converted

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
