"""NEXUS AI Agent - Agent Exceptions"""

from typing import Optional, Dict, Any
from .base_exceptions import NexusException


class AgentException(NexusException):
    """Base exception for agent-related errors"""

    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.details["agent_id"] = agent_id
        self.details["agent_name"] = agent_name


class AgentInitializationError(AgentException):
    """Agent initialization error"""

    def __init__(
        self,
        message: str = "Failed to initialize agent",
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        reason: Optional[str] = None
    ):
        super().__init__(
            message,
            agent_id=agent_id,
            agent_name=agent_name,
            code="AGENT_INIT_ERROR"
        )
        self.details["reason"] = reason


class AgentExecutionError(AgentException):
    """Agent execution error"""

    def __init__(
        self,
        message: str = "Agent execution failed",
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        task: Optional[str] = None,
        iteration: Optional[int] = None
    ):
        super().__init__(
            message,
            agent_id=agent_id,
            agent_name=agent_name,
            code="AGENT_EXEC_ERROR"
        )
        self.details["task"] = task
        self.details["iteration"] = iteration


class ToolExecutionError(AgentException):
    """Tool execution error"""

    def __init__(
        self,
        message: str = "Tool execution failed",
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None
    ):
        super().__init__(
            message,
            agent_id=agent_id,
            code="TOOL_EXEC_ERROR"
        )
        self.details["tool_name"] = tool_name
        self.details["tool_input"] = str(tool_input) if tool_input else None


class PlanningError(AgentException):
    """Planning error"""

    def __init__(
        self,
        message: str = "Planning failed",
        agent_id: Optional[str] = None,
        task: Optional[str] = None,
        step: Optional[int] = None
    ):
        super().__init__(
            message,
            agent_id=agent_id,
            code="PLANNING_ERROR"
        )
        self.details["task"] = task
        self.details["step"] = step


class ReasoningError(AgentException):
    """Reasoning error"""

    def __init__(
        self,
        message: str = "Reasoning failed",
        agent_id: Optional[str] = None,
        strategy: Optional[str] = None,
        iteration: Optional[int] = None
    ):
        super().__init__(
            message,
            agent_id=agent_id,
            code="REASONING_ERROR"
        )
        self.details["strategy"] = strategy
        self.details["iteration"] = iteration


class MemoryError(AgentException):
    """Memory operation error"""

    def __init__(
        self,
        message: str = "Memory operation failed",
        agent_id: Optional[str] = None,
        operation: Optional[str] = None,
        memory_type: Optional[str] = None
    ):
        super().__init__(
            message,
            agent_id=agent_id,
            code="MEMORY_ERROR"
        )
        self.details["operation"] = operation
        self.details["memory_type"] = memory_type


class CommunicationError(AgentException):
    """Inter-agent communication error"""

    def __init__(
        self,
        message: str = "Agent communication failed",
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None
    ):
        super().__init__(
            message,
            code="COMMUNICATION_ERROR"
        )
        self.details["sender_id"] = sender_id
        self.details["receiver_id"] = receiver_id


class MaxIterationsError(AgentException):
    """Max iterations exceeded error"""

    def __init__(
        self,
        message: str = "Maximum iterations exceeded",
        agent_id: Optional[str] = None,
        max_iterations: Optional[int] = None,
        task: Optional[str] = None
    ):
        super().__init__(
            message,
            agent_id=agent_id,
            code="MAX_ITERATIONS"
        )
        self.details["max_iterations"] = max_iterations
        self.details["task"] = task

