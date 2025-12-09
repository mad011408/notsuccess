"""
NEXUS AI Agent - Main Agent Class
TryBons AI Integration
"""

import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from config.settings import Settings, get_settings
from config.logging_config import get_logger
from config.constants import (
    AgentType,
    ReasoningStrategy,
    TaskStatus,
    DEFAULT_MODEL,
    AVAILABLE_MODELS,
    API_KEY,
    API_BASE_URL
)
from prompts.system_prompts import (
    DEFAULT_SYSTEM_PROMPT,
    CODER_SYSTEM_PROMPT,
    RESEARCHER_SYSTEM_PROMPT,
    ANALYST_SYSTEM_PROMPT,
    ASSISTANT_SYSTEM_PROMPT,
    get_system_prompt,
    SYSTEM_PROMPTS
)
from .brain_engine import BrainEngine, BrainContext
from .context_engine import ContextEngine
from .session_handler import SessionHandler
from .execution_engine import ExecutionEngine
from .response_generator import ResponseGenerator
from .stream_processor import StreamProcessor
from .callback_manager import CallbackManager


logger = get_logger(__name__)


@dataclass
class AgentConfig:
    """Agent configuration for TryBons AI"""
    name: str = "NEXUS"
    agent_type: AgentType = AgentType.GENERAL
    model: str = DEFAULT_MODEL  # claude-opus-4-5
    provider: str = "anthropic"
    api_key: str = API_KEY
    base_url: str = API_BASE_URL
    temperature: float = 0.7
    max_tokens: int = 49000
    max_iterations: int = 10
    reasoning_strategy: ReasoningStrategy = ReasoningStrategy.REACT
    enable_memory: bool = True
    enable_tools: bool = True
    streaming: bool = True
    verbose: bool = False
    # System prompt - directly connected, no filtering
    system_prompt: str = None  # Will be set based on agent_type


@dataclass
class AgentState:
    """Current agent state"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    iteration: int = 0
    status: TaskStatus = TaskStatus.PENDING
    current_task: Optional[str] = None
    last_response: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class NexusAgent:
    """
    Main NEXUS AI Agent class
    Powered by TryBons AI - Claude Models

    This is the central orchestrator that coordinates all components
    of the AI agent system.

    Available Models:
    - claude-opus-4-1-20250805
    - claude-opus-4-5 (default)
    - claude-opus-4-5-20251101
    """

    # TryBons AI Configuration
    DEFAULT_MODEL = DEFAULT_MODEL
    AVAILABLE_MODELS = AVAILABLE_MODELS
    API_KEY = API_KEY
    API_BASE_URL = API_BASE_URL

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        settings: Optional[Settings] = None
    ):
        self.config = config or AgentConfig()
        self.settings = settings or get_settings()
        self.state = AgentState()

        # Validate model
        if self.config.model not in self.AVAILABLE_MODELS:
            logger.warning(f"Model {self.config.model} not available, using default")
            self.config.model = self.DEFAULT_MODEL

        # Set system prompt based on agent_type if not provided - DIRECT CONNECTION
        if self.config.system_prompt is None:
            self.config.system_prompt = self._get_prompt_for_agent_type(self.config.agent_type)

        # Initialize components with system prompt
        self.brain = BrainEngine(self.config, self.settings)
        self.context = ContextEngine(system_prompt=self.config.system_prompt)
        self.session = SessionHandler()
        self.executor = ExecutionEngine()
        self.response_gen = ResponseGenerator()
        self.stream_processor = StreamProcessor()
        self.callbacks = CallbackManager()

        # Tool registry
        self._tools: Dict[str, Callable] = {}

        logger.info(f"NexusAgent initialized with model: {self.config.model}")
        logger.info(f"API Base URL: {self.config.base_url}")
        logger.info(f"System prompt loaded for agent type: {self.config.agent_type.value}")

    def _get_prompt_for_agent_type(self, agent_type: AgentType) -> str:
        """Get system prompt based on agent type - Direct mapping, no filtering"""
        prompt_mapping = {
            AgentType.GENERAL: DEFAULT_SYSTEM_PROMPT,
            AgentType.CODER: CODER_SYSTEM_PROMPT,
            AgentType.RESEARCHER: RESEARCHER_SYSTEM_PROMPT,
            AgentType.ANALYST: ANALYST_SYSTEM_PROMPT,
            AgentType.ASSISTANT: ASSISTANT_SYSTEM_PROMPT,
        }
        return prompt_mapping.get(agent_type, DEFAULT_SYSTEM_PROMPT)

    async def run(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Run the agent with a given prompt

        Args:
            prompt: User input prompt
            context: Optional additional context
            stream: Whether to stream the response

        Yields:
            Response chunks (if streaming) or full response
        """
        self.state.status = TaskStatus.IN_PROGRESS
        self.state.current_task = prompt
        self.state.iteration = 0

        try:
            # Trigger start callbacks
            await self.callbacks.trigger("on_start", prompt=prompt)

            # Build context
            context_window = await self.context.build_context(
                prompt=prompt,
                additional_context=context,
                history=self.session.get_history()
            )

            # Convert to BrainContext with proper dict messages
            brain_context = BrainContext(
                messages=context_window.get_messages_as_dicts(),
                system_prompt=context_window.system_prompt,
                max_tokens=context_window.max_tokens
            )

            # Process through brain engine
            if stream:
                async for chunk in self.brain.process_stream(brain_context):
                    self.state.iteration += 1
                    await self.callbacks.trigger("on_chunk", chunk=chunk)
                    yield chunk
            else:
                response = await self.brain.process(brain_context)
                self.state.last_response = response
                yield response

            # Update session
            self.session.add_interaction(prompt, self.state.last_response or "")

            self.state.status = TaskStatus.COMPLETED
            await self.callbacks.trigger("on_complete", response=self.state.last_response)

        except Exception as e:
            self.state.status = TaskStatus.FAILED
            self.state.error = str(e)
            logger.error(f"Agent error: {e}")
            await self.callbacks.trigger("on_error", error=e)
            raise

        finally:
            self.state.updated_at = datetime.utcnow()

    async def chat(self, message: str) -> str:
        """
        Simple chat interface (non-streaming)

        Args:
            message: User message

        Returns:
            Agent response
        """
        response_parts = []
        async for chunk in self.run(message, stream=False):
            response_parts.append(chunk)
        return "".join(response_parts)

    async def execute_task(
        self,
        task: str,
        tools: Optional[List[str]] = None,
        max_iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a complex task using available tools

        Args:
            task: Task description
            tools: List of tool names to use
            max_iterations: Maximum iterations for task

        Returns:
            Task execution result
        """
        max_iter = max_iterations or self.config.max_iterations

        result = await self.executor.execute(
            task=task,
            brain=self.brain,
            tools=tools or list(self._tools.keys()),
            max_iterations=max_iter
        )

        return result

    def register_tool(self, name: str, tool: Callable, description: str = "") -> None:
        """Register a tool for the agent to use"""
        self._tools[name] = tool
        self.brain.register_tool(name, tool, description)
        logger.info(f"Tool registered: {name}")

    def add_callback(self, event: str, callback: Callable) -> None:
        """Add a callback for an event"""
        self.callbacks.add(event, callback)

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return {
            "session_id": self.state.session_id,
            "status": self.state.status.value,
            "iteration": self.state.iteration,
            "current_task": self.state.current_task,
            "error": self.state.error,
            "model": self.config.model,
            "provider": self.config.provider,
            "created_at": self.state.created_at.isoformat(),
            "updated_at": self.state.updated_at.isoformat(),
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        return {
            "model": self.config.model,
            "provider": self.config.provider,
            "base_url": self.config.base_url,
            "available_models": self.AVAILABLE_MODELS,
        }

    def set_model(self, model: str) -> bool:
        """
        Set the model to use

        Args:
            model: Model ID to use

        Returns:
            True if model was set successfully
        """
        if model in self.AVAILABLE_MODELS:
            self.config.model = model
            logger.info(f"Model set to: {model}")
            return True
        else:
            logger.warning(f"Model {model} not available")
            return False

    def set_system_prompt(self, prompt: str) -> None:
        """Set custom system prompt - Direct, no filtering"""
        self.config.system_prompt = prompt
        self.context.set_system_prompt(prompt)
        logger.info("Custom system prompt set")

    def set_system_prompt_by_type(self, prompt_type: str) -> bool:
        """Set system prompt by type name"""
        prompt = get_system_prompt(prompt_type)
        if prompt:
            self.config.system_prompt = prompt
            self.context.set_system_prompt(prompt)
            logger.info(f"System prompt set to type: {prompt_type}")
            return True
        return False

    def get_system_prompt(self) -> str:
        """Get current system prompt"""
        return self.config.system_prompt

    def reset(self) -> None:
        """Reset agent state"""
        self.state = AgentState()
        self.session.clear()
        self.context.clear()
        logger.info("Agent state reset")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()

    async def shutdown(self) -> None:
        """Cleanup and shutdown agent"""
        await self.callbacks.trigger("on_shutdown")
        self.reset()
        logger.info("Agent shutdown complete")


# Factory function
def create_agent(
    agent_type: AgentType = AgentType.GENERAL,
    model: str = DEFAULT_MODEL,
    **kwargs
) -> NexusAgent:
    """
    Factory function to create agents

    Args:
        agent_type: Type of agent to create
        model: LLM model to use (default: claude-opus-4-5)
        **kwargs: Additional configuration options

    Available Models:
        - claude-opus-4-1-20250805
        - claude-opus-4-5 (default)
        - claude-opus-4-5-20251101

    Returns:
        Configured NexusAgent instance
    """
    config = AgentConfig(
        agent_type=agent_type,
        model=model,
        **kwargs
    )
    return NexusAgent(config=config)
