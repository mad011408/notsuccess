"""NEXUS AI Agent - LLM Types"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FinishReason(str, Enum):
    """Generation finish reason"""
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


@dataclass
class TokenUsage:
    """Token usage statistics"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }


@dataclass
class LLMResponse:
    """LLM response"""
    content: str
    model: str
    provider: str
    finish_reason: FinishReason = FinishReason.STOP
    usage: Optional[TokenUsage] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "finish_reason": self.finish_reason.value,
            "usage": self.usage.to_dict() if self.usage else None,
            "tool_calls": self.tool_calls,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class StreamChunk:
    """Streaming response chunk"""
    content: str
    index: int = 0
    finish_reason: Optional[FinishReason] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[TokenUsage] = None


@dataclass
class EmbeddingResult:
    """Embedding result"""
    embedding: List[float]
    model: str
    usage: Optional[TokenUsage] = None
    index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "embedding": self.embedding,
            "model": self.model,
            "usage": self.usage.to_dict() if self.usage else None,
            "index": self.index
        }


@dataclass
class BatchEmbeddingResult:
    """Batch embedding result"""
    embeddings: List[List[float]]
    model: str
    usage: Optional[TokenUsage] = None


@dataclass
class CompletionChoice:
    """Completion choice (OpenAI-compatible)"""
    index: int
    message: Dict[str, Any]
    finish_reason: str
    logprobs: Optional[Dict[str, Any]] = None


@dataclass
class CompletionResponse:
    """Completion response (OpenAI-compatible)"""
    id: str
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: List[CompletionChoice] = field(default_factory=list)
    usage: Optional[TokenUsage] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "model": self.model,
            "choices": [
                {
                    "index": c.index,
                    "message": c.message,
                    "finish_reason": c.finish_reason,
                    "logprobs": c.logprobs
                }
                for c in self.choices
            ],
            "usage": self.usage.to_dict() if self.usage else None
        }


@dataclass
class ModelInfo:
    """Model information"""
    id: str
    name: str
    provider: str
    context_length: int
    max_output_tokens: int
    supports_functions: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0


# Type aliases
EmbeddingVector = List[float]
MessageDict = Dict[str, Any]
ToolSchema = Dict[str, Any]

