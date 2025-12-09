"""NEXUS AI Agent - Common Types"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message roles"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class Message:
    """Chat message"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = {
            "role": self.role.value if isinstance(self.role, Enum) else self.role,
            "content": self.content
        }
        if self.name:
            d["name"] = self.name
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d


@dataclass
class ToolCall:
    """Tool call request"""
    id: str
    name: str
    arguments: Dict[str, Any]
    type: str = "function"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "function": {
                "name": self.name,
                "arguments": self.arguments
            }
        }


@dataclass
class ToolResult:
    """Tool execution result"""
    tool_call_id: str
    content: str
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tool_call_id": self.tool_call_id,
            "content": self.content,
            "success": self.success,
            "error": self.error
        }


@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    provider: str
    max_tokens: int = 49000
    context_length: int = 200000
    supports_functions: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    timeout: int = 1600


@dataclass
class GenerationConfig:
    """Generation configuration"""
    temperature: float = 0.7
    max_tokens: Optional[int] = 49000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False
    timeout: int = 1600


@dataclass
class FunctionSchema:
    """Function schema for tool calling"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAI function schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required
                }
            }
        }


# Type aliases
MessageList = List[Message]
ToolList = List[FunctionSchema]
Context = Dict[str, Any]
Embedding = List[float]

