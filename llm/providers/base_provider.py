"""
NEXUS AI Agent - Base LLM Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LLMResponse:
    """Standard LLM response format"""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""
    latency_ms: float = 0.0
    cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw_response: Optional[Dict[str, Any]] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class Message:
    """Chat message format"""
    role: str
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    temperature: float = 0.7
    max_tokens: int = 49000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    stream: bool = False
    json_mode: bool = False
    seed: Optional[int] = None
    timeout: int = 1600


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers

    All LLM providers must implement this interface.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs
        self._client = None
        self._initialized = False

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name"""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Get list of supported models"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client"""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response

        Args:
            messages: List of chat messages
            model: Model to use
            config: Generation configuration

        Returns:
            LLMResponse object
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response

        Args:
            messages: List of chat messages
            model: Model to use
            config: Generation configuration

        Yields:
            Response chunks
        """
        pass

    async def generate_with_functions(
        self,
        messages: List[Dict[str, str]],
        model: str,
        functions: List[Dict[str, Any]],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate with function calling

        Args:
            messages: List of chat messages
            model: Model to use
            functions: Function definitions
            config: Generation configuration

        Returns:
            LLMResponse with potential function call
        """
        raise NotImplementedError("Function calling not supported by this provider")

    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: List[Dict[str, Any]],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate with tool use

        Args:
            messages: List of chat messages
            model: Model to use
            tools: Tool definitions
            config: Generation configuration

        Returns:
            LLMResponse with potential tool calls
        """
        raise NotImplementedError("Tool use not supported by this provider")

    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embeddings

        Args:
            text: Text to embed
            model: Embedding model

        Returns:
            Embedding vector
        """
        raise NotImplementedError("Embeddings not supported by this provider")

    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: Texts to embed
            model: Embedding model

        Returns:
            List of embedding vectors
        """
        return [await self.embed(text, model) for text in texts]

    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text

        Args:
            text: Text to count
            model: Model for tokenization

        Returns:
            Token count
        """
        # Default estimation
        return len(text) // 4

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a model"""
        return {
            "model": model,
            "provider": self.provider_name,
            "supported": model in self.supported_models
        }

    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        try:
            await self.generate(
                messages=[{"role": "user", "content": "hi"}],
                model=self.supported_models[0] if self.supported_models else "",
                config=GenerationConfig(max_tokens=5)
            )
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Cleanup resources"""
        self._client = None
        self._initialized = False

    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Message]:
        """Convert dict messages to Message objects"""
        return [
            Message(
                role=m.get("role", "user"),
                content=m.get("content", ""),
                name=m.get("name"),
                function_call=m.get("function_call"),
                tool_calls=m.get("tool_calls"),
                tool_call_id=m.get("tool_call_id")
            )
            for m in messages
        ]

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for API call"""
        # Override in subclass with actual pricing
        return 0.0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name})"
