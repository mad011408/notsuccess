"""NEXUS AI Agent - LLM Exceptions"""

from typing import Optional, Dict, Any
from .base_exceptions import NexusException


class LLMException(NexusException):
    """Base exception for LLM-related errors"""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.details["provider"] = provider
        self.details["model"] = model


class LLMProviderError(LLMException):
    """LLM provider error"""

    def __init__(
        self,
        message: str = "LLM provider error",
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        response: Optional[str] = None
    ):
        super().__init__(
            message,
            provider=provider,
            code="LLM_PROVIDER_ERROR"
        )
        self.details["status_code"] = status_code
        self.details["response"] = response


class LLMResponseError(LLMException):
    """LLM response error"""

    def __init__(
        self,
        message: str = "Invalid LLM response",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        response: Optional[str] = None
    ):
        super().__init__(
            message,
            provider=provider,
            model=model,
            code="LLM_RESPONSE_ERROR"
        )
        self.details["response"] = response[:500] if response else None


class TokenLimitError(LLMException):
    """Token limit exceeded error"""

    def __init__(
        self,
        message: str = "Token limit exceeded",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        token_count: Optional[int] = None,
        max_tokens: Optional[int] = None
    ):
        super().__init__(
            message,
            provider=provider,
            model=model,
            code="TOKEN_LIMIT"
        )
        self.details["token_count"] = token_count
        self.details["max_tokens"] = max_tokens


class ModelNotFoundError(LLMException):
    """Model not found error"""

    def __init__(
        self,
        message: str = "Model not found",
        provider: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__(
            message,
            provider=provider,
            model=model,
            code="MODEL_NOT_FOUND"
        )


class ContentFilterError(LLMException):
    """Content filter triggered error"""

    def __init__(
        self,
        message: str = "Content filtered",
        provider: Optional[str] = None,
        filter_type: Optional[str] = None
    ):
        super().__init__(
            message,
            provider=provider,
            code="CONTENT_FILTERED"
        )
        self.details["filter_type"] = filter_type


class ContextLengthError(LLMException):
    """Context length exceeded error"""

    def __init__(
        self,
        message: str = "Context length exceeded",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        context_length: Optional[int] = None,
        max_context: Optional[int] = None
    ):
        super().__init__(
            message,
            provider=provider,
            model=model,
            code="CONTEXT_LENGTH"
        )
        self.details["context_length"] = context_length
        self.details["max_context"] = max_context


class StreamingError(LLMException):
    """Streaming error"""

    def __init__(
        self,
        message: str = "Streaming error",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        chunks_received: Optional[int] = None
    ):
        super().__init__(
            message,
            provider=provider,
            model=model,
            code="STREAMING_ERROR"
        )
        self.details["chunks_received"] = chunks_received


class FunctionCallError(LLMException):
    """Function calling error"""

    def __init__(
        self,
        message: str = "Function call error",
        provider: Optional[str] = None,
        function_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            provider=provider,
            code="FUNCTION_CALL_ERROR"
        )
        self.details["function_name"] = function_name
        self.details["arguments"] = str(arguments) if arguments else None


class EmbeddingError(LLMException):
    """Embedding generation error"""

    def __init__(
        self,
        message: str = "Embedding error",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        input_length: Optional[int] = None
    ):
        super().__init__(
            message,
            provider=provider,
            model=model,
            code="EMBEDDING_ERROR"
        )
        self.details["input_length"] = input_length

