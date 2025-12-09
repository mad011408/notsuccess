"""NEXUS AI Agent - Base Exceptions"""

from typing import Optional, Dict, Any


class NexusException(Exception):
    """Base exception for NEXUS AI Agent"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details
        }

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ConfigurationError(NexusException):
    """Configuration error"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message,
            code="CONFIG_ERROR",
            details={"config_key": config_key}
        )


class ValidationError(NexusException):
    """Validation error"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field, "value": str(value) if value else None}
        )


class AuthenticationError(NexusException):
    """Authentication error"""

    def __init__(self, message: str = "Authentication failed", provider: Optional[str] = None):
        super().__init__(
            message,
            code="AUTH_ERROR",
            details={"provider": provider}
        )


class RateLimitError(NexusException):
    """Rate limit exceeded error"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[float] = None
    ):
        super().__init__(
            message,
            code="RATE_LIMIT",
            details={"retry_after": retry_after}
        )
        self.retry_after = retry_after


class TimeoutError(NexusException):
    """Timeout error"""

    def __init__(
        self,
        message: str = "Operation timed out",
        timeout: Optional[float] = None,
        operation: Optional[str] = None
    ):
        super().__init__(
            message,
            code="TIMEOUT",
            details={"timeout": timeout, "operation": operation}
        )


class ConnectionError(NexusException):
    """Connection error"""

    def __init__(
        self,
        message: str = "Connection failed",
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        super().__init__(
            message,
            code="CONNECTION_ERROR",
            details={"host": host, "port": port}
        )


class ResourceNotFoundError(NexusException):
    """Resource not found error"""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        super().__init__(
            message,
            code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class PermissionError(NexusException):
    """Permission denied error"""

    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: Optional[str] = None
    ):
        super().__init__(
            message,
            code="PERMISSION_DENIED",
            details={"required_permission": required_permission}
        )


class QuotaExceededError(NexusException):
    """Quota exceeded error"""

    def __init__(
        self,
        message: str = "Quota exceeded",
        quota_type: Optional[str] = None,
        limit: Optional[int] = None,
        used: Optional[int] = None
    ):
        super().__init__(
            message,
            code="QUOTA_EXCEEDED",
            details={"quota_type": quota_type, "limit": limit, "used": used}
        )

