"""NEXUS AI Agent - Exceptions Module"""

from .base_exceptions import (
    NexusException,
    ConfigurationError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    ConnectionError,
)

from .agent_exceptions import (
    AgentException,
    AgentInitializationError,
    AgentExecutionError,
    ToolExecutionError,
    PlanningError,
    ReasoningError,
)

from .llm_exceptions import (
    LLMException,
    LLMProviderError,
    LLMResponseError,
    TokenLimitError,
    ModelNotFoundError,
)


__all__ = [
    # Base exceptions
    "NexusException",
    "ConfigurationError",
    "ValidationError",
    "AuthenticationError",
    "RateLimitError",
    "TimeoutError",
    "ConnectionError",
    # Agent exceptions
    "AgentException",
    "AgentInitializationError",
    "AgentExecutionError",
    "ToolExecutionError",
    "PlanningError",
    "ReasoningError",
    # LLM exceptions
    "LLMException",
    "LLMProviderError",
    "LLMResponseError",
    "TokenLimitError",
    "ModelNotFoundError",
]

