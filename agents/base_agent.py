"""NEXUS AI Agent - Base Agent"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio

from config.logging_config import get_logger


logger = get_logger(__name__)


class AgentCapability(str, Enum):
    """Agent capabilities"""
    REASONING = "reasoning"
    CODE_EXECUTION = "code_execution"
    WEB_SEARCH = "web_search"
    FILE_OPERATIONS = "file_operations"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    API_CALLS = "api_calls"
    DATABASE = "database"
    MEMORY = "memory"
    PLANNING = "planning"


@dataclass
class AgentOutput:
    """Agent output"""
    content: str
    type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent_id: str = ""
    success: bool = True
    error: Optional[str] = None


@dataclass
class AgentContext:
    """Agent execution context"""
    task: str
    history: List[Dict[str, str]] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    parent_agent: Optional[str] = None
    max_iterations: int = 10
    timeout: float = 1600.0


class BaseAgent(ABC):
    """
    Base class for all agents

    Provides common functionality for agent implementation
    """

    def __init__(
        self,
        name: str = "Agent",
        description: str = "",
        capabilities: Optional[List[AgentCapability]] = None,
        model: str = "claude-opus-4-5",
        temperature: float = 0.7,
        max_tokens: int = 49000
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._tools: Dict[str, Callable] = {}
        self._state: Dict[str, Any] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._running = False

        logger.info(f"Agent initialized: {self.name} ({self.id})")

    @abstractmethod
    async def run(self, task: str, context: Optional[AgentContext] = None) -> AgentOutput:
        """
        Execute agent task

        Args:
            task: Task to execute
            context: Optional execution context

        Returns:
            AgentOutput with result
        """
        pass

    @abstractmethod
    async def run_stream(
        self,
        task: str,
        context: Optional[AgentContext] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute agent task with streaming

        Args:
            task: Task to execute
            context: Optional execution context

        Yields:
            Response chunks
        """
        pass

    def register_tool(self, name: str, tool: Callable, description: str = "") -> None:
        """Register a tool for the agent"""
        self._tools[name] = tool
        logger.debug(f"Tool registered: {name}")

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool"""
        self._tools.pop(name, None)

    def get_tools(self) -> Dict[str, Callable]:
        """Get registered tools"""
        return self._tools.copy()

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has capability"""
        return capability in self.capabilities

    def add_capability(self, capability: AgentCapability) -> None:
        """Add capability to agent"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)

    def set_state(self, key: str, value: Any) -> None:
        """Set state value"""
        self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value"""
        return self._state.get(key, default)

    def clear_state(self) -> None:
        """Clear agent state"""
        self._state.clear()

    def on(self, event: str, callback: Callable) -> None:
        """Register event callback"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    async def emit(self, event: str, *args, **kwargs) -> None:
        """Emit event to callbacks"""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def think(self, prompt: str) -> str:
        """
        Internal reasoning step

        Override in subclass for custom reasoning
        """
        return prompt

    async def act(self, action: str, params: Dict[str, Any]) -> Any:
        """
        Execute an action

        Args:
            action: Action/tool name
            params: Action parameters

        Returns:
            Action result
        """
        if action in self._tools:
            tool = self._tools[action]
            if asyncio.iscoroutinefunction(tool):
                return await tool(**params)
            return tool(**params)
        raise ValueError(f"Unknown action: {action}")

    async def observe(self, result: Any) -> str:
        """
        Process observation from action

        Args:
            result: Result from action

        Returns:
            Observation string
        """
        return str(result)

    def stop(self) -> None:
        """Stop agent execution"""
        self._running = False

    def is_running(self) -> bool:
        """Check if agent is running"""
        return self._running

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "model": self.model,
            "tools": list(self._tools.keys()),
            "running": self._running,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, id={self.id[:8]})>"


class SimpleAgent(BaseAgent):
    """Simple agent implementation"""

    def __init__(self, llm_client=None, **kwargs):
        super().__init__(**kwargs)
        self.llm_client = llm_client

    async def run(self, task: str, context: Optional[AgentContext] = None) -> AgentOutput:
        """Execute task"""
        self._running = True
        await self.emit("start", task)

        try:
            # Build prompt
            prompt = await self.think(task)

            # Get response from LLM
            if self.llm_client:
                response = await self.llm_client.generate(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                content = response.content
            else:
                content = f"Task received: {task}"

            await self.emit("complete", content)

            return AgentOutput(
                content=content,
                agent_id=self.id,
                success=True
            )

        except Exception as e:
            logger.error(f"Agent error: {e}")
            await self.emit("error", e)
            return AgentOutput(
                content="",
                agent_id=self.id,
                success=False,
                error=str(e)
            )

        finally:
            self._running = False

    async def run_stream(
        self,
        task: str,
        context: Optional[AgentContext] = None
    ) -> AsyncGenerator[str, None]:
        """Execute task with streaming"""
        self._running = True
        await self.emit("start", task)

        try:
            prompt = await self.think(task)

            if self.llm_client:
                async for chunk in self.llm_client.generate_stream(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model
                ):
                    yield chunk
            else:
                yield f"Task received: {task}"

            await self.emit("complete", "")

        except Exception as e:
            logger.error(f"Agent stream error: {e}")
            await self.emit("error", e)

        finally:
            self._running = False

