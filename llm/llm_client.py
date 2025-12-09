"""
NEXUS AI Agent - Unified LLM Client
Multi-Provider: TryBons AI, NVIDIA, Bytez, OpenRouter
"""

from typing import Optional, List, Dict, Any, AsyncGenerator, Type
from datetime import datetime

from .providers.base_provider import BaseLLMProvider, LLMResponse, GenerationConfig
from .providers.anthropic_provider import AnthropicProvider
from .providers.nvidia_provider import NvidiaProvider
from .providers.bytez_provider import BytezProvider
from .providers.openrouter_provider import OpenRouterProvider

from config.logging_config import get_logger
from config.constants import (
    API_KEY,
    API_BASE_URL,
    NVIDIA_API_KEY,
    NVIDIA_API_BASE_URL,
    BYTEZ_API_KEY,
    BYTEZ_API_BASE_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_API_BASE_URL,
    AVAILABLE_MODELS,
    NVIDIA_MODELS,
    BYTEZ_MODELS,
    OPENROUTER_MODELS,
    CLAUDE_MODELS,
    DEFAULT_MODEL,
    LLMProvider
)
from prompts.system_prompts import DEFAULT_SYSTEM_PROMPT, get_system_prompt


logger = get_logger(__name__)


def get_provider_for_model(model: str) -> str:
    """Determine provider based on model name"""
    if model in NVIDIA_MODELS:
        return "nvidia"
    elif model in BYTEZ_MODELS:
        return "bytez"
    elif model in OPENROUTER_MODELS:
        return "openrouter"
    elif model in CLAUDE_MODELS:
        return "anthropic"
    else:
        # Default to anthropic
        return "anthropic"


class LLMClient:
    """
    Unified LLM Client for Multiple Providers

    Providers:
    - anthropic: TryBons AI (Claude models)
    - nvidia: NVIDIA API (MiniMax, Kimi, Mistral, DeepSeek)
    - bytez: Bytez API (GPT models)
    """

    # Default Configuration
    DEFAULT_API_KEY = API_KEY
    DEFAULT_BASE_URL = API_BASE_URL
    DEFAULT_MODEL = DEFAULT_MODEL
    AVAILABLE_MODELS = AVAILABLE_MODELS

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize LLM client

        Args:
            provider: LLM provider name ('anthropic', 'nvidia', 'bytez')
            model: Default model to use
            api_key: API key for the provider
            base_url: Base URL for API
            system_prompt: Default system prompt to use
            **kwargs: Additional provider-specific options
        """
        self.default_model = model or self.DEFAULT_MODEL

        # Auto-detect provider from model if not specified
        if model:
            self.provider_name = get_provider_for_model(model)
        else:
            self.provider_name = provider

        # Set API key and base URL based on provider
        if self.provider_name == "nvidia":
            self._api_key = api_key or NVIDIA_API_KEY
            self._base_url = base_url or NVIDIA_API_BASE_URL
        elif self.provider_name == "bytez":
            self._api_key = api_key or BYTEZ_API_KEY
            self._base_url = base_url or BYTEZ_API_BASE_URL
        elif self.provider_name == "openrouter":
            self._api_key = api_key or OPENROUTER_API_KEY
            self._base_url = base_url or OPENROUTER_API_BASE_URL
        else:  # anthropic
            self._api_key = api_key or API_KEY
            self._base_url = base_url or API_BASE_URL

        self._provider: Optional[BaseLLMProvider] = None
        self._kwargs = kwargs
        self._initialized = False

        # System prompt - Direct connection, no filtering
        # DEFAULT_SYSTEM_PROMPT from base_system_prompts.py
        self._system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

        # Metrics
        self._total_requests = 0
        self._total_tokens = 0
        self._total_cost = 0.0

    async def initialize(self) -> None:
        """Initialize the LLM provider"""
        if self._initialized:
            return

        # Create provider based on provider_name
        if self.provider_name == "nvidia":
            self._provider = NvidiaProvider(
                api_key=self._api_key,
                base_url=self._base_url,
                **self._kwargs
            )
        elif self.provider_name == "bytez":
            self._provider = BytezProvider(
                api_key=self._api_key,
                base_url=self._base_url,
                **self._kwargs
            )
        elif self.provider_name == "openrouter":
            self._provider = OpenRouterProvider(
                api_key=self._api_key,
                base_url=self._base_url,
                **self._kwargs
            )
        else:  # anthropic
            self._provider = AnthropicProvider(
                api_key=self._api_key,
                base_url=self._base_url,
                **self._kwargs
            )

        await self._provider.initialize()
        self._initialized = True

        logger.info(f"LLM client initialized - Provider: {self.provider_name}, Model: {self.default_model}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 49000,
        **kwargs
    ) -> str:
        """
        Generate a response

        Args:
            messages: List of chat messages
            model: Model to use (overrides default)
            system: System prompt (uses default if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation options

        Returns:
            Generated text
        """
        if not self._initialized:
            await self.initialize()

        model = model or self.default_model

        # Validate model
        if model not in self.AVAILABLE_MODELS:
            logger.warning(f"Model {model} not in available models, using default")
            model = self.default_model

        # ALWAYS use system prompt - MANDATORY for EVERY request
        # Priority: provided system > stored system prompt > DEFAULT_SYSTEM_PROMPT
        effective_system = system if system else self._system_prompt
        if not effective_system:
            effective_system = DEFAULT_SYSTEM_PROMPT
        # Ensure effective_system is never None
        effective_system = effective_system or "You are a helpful AI assistant."

        # ALWAYS add system message - EVERY REQUEST gets system prompt from base_system_prompts.py
        messages = [{"role": "system", "content": effective_system}] + messages
        logger.debug(f"System prompt attached (length: {len(effective_system)} chars)")

        config = GenerationConfig(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=kwargs.get("top_p", 1.0),
            stop_sequences=kwargs.get("stop_sequences"),
        )

        response = await self._provider.generate(messages, model, config)

        # Update metrics
        self._total_requests += 1
        self._total_tokens += response.total_tokens
        self._total_cost += response.cost

        return response.content

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 49000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response

        Args:
            messages: List of chat messages
            model: Model to use
            system: System prompt (uses default if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional options

        Yields:
            Response chunks
        """
        if not self._initialized:
            await self.initialize()

        model = model or self.default_model

        if model not in self.AVAILABLE_MODELS:
            model = self.default_model

        # ALWAYS use system prompt - MANDATORY for EVERY request
        # Priority: provided system > stored system prompt > DEFAULT_SYSTEM_PROMPT
        effective_system = system if system else self._system_prompt
        if not effective_system:
            effective_system = DEFAULT_SYSTEM_PROMPT
        # Ensure effective_system is never None
        effective_system = effective_system or "You are a helpful AI assistant."

        # ALWAYS add system message - EVERY REQUEST gets system prompt from base_system_prompts.py
        messages = [{"role": "system", "content": effective_system}] + messages
        logger.debug(f"Stream: System prompt attached (length: {len(effective_system)} chars)")

        config = GenerationConfig(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=kwargs.get("top_p", 1.0),
            stream=True,
        )

        self._total_requests += 1

        async for chunk in self._provider.generate_stream(messages, model, config):
            yield chunk

    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate with tool use

        Args:
            messages: Chat messages
            tools: Tool definitions
            model: Model to use
            **kwargs: Additional options

        Returns:
            LLMResponse with potential tool calls
        """
        if not self._initialized:
            await self.initialize()

        model = model or self.default_model

        if model not in self.AVAILABLE_MODELS:
            model = self.default_model

        # ALWAYS use system prompt - MANDATORY for EVERY request
        effective_system = self._system_prompt or DEFAULT_SYSTEM_PROMPT
        messages = [{"role": "system", "content": effective_system}] + messages
        logger.debug(f"Tools: System prompt attached (length: {len(effective_system)} chars)")

        config = GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
        )

        response = await self._provider.generate_with_tools(
            messages, model, tools, config, **kwargs
        )

        self._total_requests += 1
        self._total_tokens += response.total_tokens
        self._total_cost += response.cost

        return response

    async def chat(
        self,
        message: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Simple chat interface

        Args:
            message: User message
            system: System prompt
            model: Model to use
            **kwargs: Additional options

        Returns:
            Assistant response
        """
        messages = [{"role": "user", "content": message}]
        return await self.generate(messages, model=model, system=system, **kwargs)

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text

        Args:
            text: Text to count
            model: Model for tokenization

        Returns:
            Token count
        """
        if not self._initialized or not self._provider:
            return len(text) // 4

        model = model or self.default_model
        return self._provider.count_tokens(text, model)

    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        if not self._initialized:
            try:
                await self.initialize()
            except:
                return False

        return await self._provider.health_check()

    def get_metrics(self) -> Dict[str, Any]:
        """Get usage metrics"""
        return {
            "provider": self.provider_name,
            "model": self.default_model,
            "base_url": self._base_url,
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "total_cost": round(self._total_cost, 6),
            "avg_tokens_per_request": (
                self._total_tokens / self._total_requests
                if self._total_requests > 0 else 0
            ),
            "available_models": self.AVAILABLE_MODELS,
        }

    def reset_metrics(self) -> None:
        """Reset usage metrics"""
        self._total_requests = 0
        self._total_tokens = 0
        self._total_cost = 0.0

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.AVAILABLE_MODELS.copy()

    async def set_model(self, model: str) -> None:
        """Set default model and switch provider if needed"""
        if model in self.AVAILABLE_MODELS:
            old_provider = self.provider_name
            new_provider = get_provider_for_model(model)

            self.default_model = model

            # If provider changed, reinitialize with new provider
            if new_provider != old_provider:
                self.provider_name = new_provider

                # Update API key and base URL for new provider
                if self.provider_name == "nvidia":
                    self._api_key = NVIDIA_API_KEY
                    self._base_url = NVIDIA_API_BASE_URL
                elif self.provider_name == "bytez":
                    self._api_key = BYTEZ_API_KEY
                    self._base_url = BYTEZ_API_BASE_URL
                elif self.provider_name == "openrouter":
                    self._api_key = OPENROUTER_API_KEY
                    self._base_url = OPENROUTER_API_BASE_URL
                else:  # anthropic
                    self._api_key = API_KEY
                    self._base_url = API_BASE_URL

                # Close old provider and reinitialize
                if self._provider:
                    await self._provider.close()
                self._initialized = False
                await self.initialize()

                logger.info(f"Provider switched from {old_provider} to {new_provider}")

            logger.info(f"Default model set to: {model}")
        else:
            logger.warning(f"Model {model} not available")

    def set_system_prompt(self, prompt: str) -> None:
        """Set system prompt - Direct, no filtering"""
        self._system_prompt = prompt
        logger.info("System prompt updated")

    def set_system_prompt_by_type(self, prompt_type: str) -> bool:
        """Set system prompt by type"""
        prompt = get_system_prompt(prompt_type)
        if prompt:
            self._system_prompt = prompt
            logger.info(f"System prompt set to type: {prompt_type}")
            return True
        return False

    def get_system_prompt(self) -> str:
        """Get current system prompt"""
        return self._system_prompt

    async def close(self) -> None:
        """Cleanup resources"""
        if self._provider:
            await self._provider.close()
        self._provider = None
        self._initialized = False

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def create_llm_client(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> LLMClient:
    """
    Factory function to create LLM client

    Args:
        model: Default model
        api_key: API key
        base_url: Base URL
        **kwargs: Additional options

    Returns:
        LLMClient instance
    """
    return LLMClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )


# Alias for backward compatibility
TryBonsClient = LLMClient
ClaudeClient = LLMClient
