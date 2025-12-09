"""NEXUS AI Agent - Agent Types"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class AgentStatus(str, Enum):
    """Agent status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentState:
    """Agent state"""
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    iteration: int = 0
    last_action: Optional[str] = None
    last_observation: Optional[str] = None
    error: Optional[str] = None
    memory: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "status": self.status.value,
            "current_task": self.current_task,
            "iteration": self.iteration,
            "last_action": self.last_action,
            "last_observation": self.last_observation,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class AgentConfig:
    """Agent configuration"""
    name: str = "Agent"
    model: str = "gpt-4o"
    provider: str = "openai"
    temperature: float = 0.7
    max_tokens: int = 4096
    max_iterations: int = 10
    timeout: float = 300.0
    enable_memory: bool = True
    enable_tools: bool = True
    verbose: bool = False
    system_prompt: Optional[str] = None


@dataclass
class ExecutionResult:
    """Task execution result"""
    task: str
    status: TaskStatus
    output: Any = None
    error: Optional[str] = None
    iterations: int = 0
    actions: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task": self.task,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "iterations": self.iterations,
            "actions": self.actions,
            "duration": self.duration,
            "metadata": self.metadata
        }


@dataclass
class ActionStep:
    """Single action step"""
    action: str
    input: Dict[str, Any]
    output: Any = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ThoughtStep:
    """Reasoning thought step"""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PlanStep:
    """Planning step"""
    step_number: int
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[int] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None


@dataclass
class Plan:
    """Execution plan"""
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: TaskStatus = TaskStatus.PENDING


# Type aliases
ActionHistory = List[ActionStep]
ThoughtHistory = List[ThoughtStep]
AgentContext = Dict[str, Any]

