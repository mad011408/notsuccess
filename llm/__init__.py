"""
NEXUS AI Agent - LLM Module
Multi-Provider: TryBons AI, NVIDIA, Bytez, OpenRouter
"""

from .llm_client import LLMClient, create_llm_client, TryBonsClient, ClaudeClient
from .providers import (
    AnthropicProvider,
    TryBonsProvider,
    ClaudeProvider,
    NvidiaProvider,
    BytezProvider,
    OpenRouterProvider,
    BaseLLMProvider,
    LLMResponse,
    GenerationConfig
)

__all__ = [
    # Main client
    "LLMClient",
    "create_llm_client",
    "TryBonsClient",
    "ClaudeClient",
    # Providers - TryBons AI / Claude
    "AnthropicProvider",
    "TryBonsProvider",
    "ClaudeProvider",
    # Providers - NVIDIA
    "NvidiaProvider",
    # Providers - Bytez
    "BytezProvider",
    # Providers - OpenRouter
    "OpenRouterProvider",
    # Base classes
    "BaseLLMProvider",
    "LLMResponse",
    "GenerationConfig",
]
