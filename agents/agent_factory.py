"""NEXUS AI Agent - Agent Factory"""

from typing import Optional, Dict, Any, Type, List
from enum import Enum

from config.logging_config import get_logger
from .base_agent import BaseAgent, AgentCapability


logger = get_logger(__name__)


class AgentType(str, Enum):
    """Available agent types"""
    SIMPLE = "simple"
    RESEARCHER = "researcher"
    CODER = "coder"
    WRITER = "writer"
    ANALYST = "analyst"
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    CUSTOM = "custom"


class AgentFactory:
    """
    Factory for creating agents

    Provides centralized agent creation and management
    """

    _registry: Dict[str, Type[BaseAgent]] = {}
    _instances: Dict[str, BaseAgent] = {}

    @classmethod
    def register(cls, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register an agent class

        Args:
            agent_type: Type identifier
            agent_class: Agent class to register
        """
        cls._registry[agent_type] = agent_class
        logger.info(f"Agent type registered: {agent_type}")

    @classmethod
    def create(
        cls,
        agent_type: str,
        name: Optional[str] = None,
        llm_client=None,
        **kwargs
    ) -> BaseAgent:
        """
        Create an agent

        Args:
            agent_type: Type of agent to create
            name: Optional agent name
            llm_client: LLM client for agent
            **kwargs: Additional agent configuration

        Returns:
            Created agent instance
        """
        # Import here to avoid circular imports
        from .base_agent import SimpleAgent

        if agent_type == AgentType.SIMPLE or agent_type not in cls._registry:
            agent = SimpleAgent(
                name=name or "SimpleAgent",
                llm_client=llm_client,
                **kwargs
            )
        else:
            agent_class = cls._registry[agent_type]
            agent = agent_class(
                name=name or agent_type.capitalize() + "Agent",
                llm_client=llm_client,
                **kwargs
            )

        cls._instances[agent.id] = agent
        logger.info(f"Agent created: {agent.name} ({agent.id})")

        return agent

    @classmethod
    def create_researcher(cls, llm_client=None, **kwargs) -> BaseAgent:
        """Create researcher agent"""
        from .specialized.researcher_agent import ResearcherAgent
        return cls.create(
            AgentType.RESEARCHER,
            llm_client=llm_client,
            capabilities=[
                AgentCapability.WEB_SEARCH,
                AgentCapability.DOCUMENT_PROCESSING,
                AgentCapability.REASONING,
            ],
            **kwargs
        )

    @classmethod
    def create_coder(cls, llm_client=None, **kwargs) -> BaseAgent:
        """Create coder agent"""
        from .specialized.coder_agent import CoderAgent
        return cls.create(
            AgentType.CODER,
            llm_client=llm_client,
            capabilities=[
                AgentCapability.CODE_EXECUTION,
                AgentCapability.FILE_OPERATIONS,
                AgentCapability.REASONING,
            ],
            **kwargs
        )

    @classmethod
    def create_writer(cls, llm_client=None, **kwargs) -> BaseAgent:
        """Create writer agent"""
        from .specialized.writer_agent import WriterAgent
        return cls.create(
            AgentType.WRITER,
            llm_client=llm_client,
            capabilities=[
                AgentCapability.REASONING,
                AgentCapability.MEMORY,
            ],
            **kwargs
        )

    @classmethod
    def create_analyst(cls, llm_client=None, **kwargs) -> BaseAgent:
        """Create analyst agent"""
        from .specialized.analyst_agent import AnalystAgent
        return cls.create(
            AgentType.ANALYST,
            llm_client=llm_client,
            capabilities=[
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.REASONING,
                AgentCapability.DATABASE,
            ],
            **kwargs
        )

    @classmethod
    def get(cls, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return cls._instances.get(agent_id)

    @classmethod
    def get_by_name(cls, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        for agent in cls._instances.values():
            if agent.name == name:
                return agent
        return None

    @classmethod
    def list_agents(cls) -> List[Dict[str, Any]]:
        """List all agent instances"""
        return [agent.get_info() for agent in cls._instances.values()]

    @classmethod
    def list_types(cls) -> List[str]:
        """List registered agent types"""
        return list(cls._registry.keys())

    @classmethod
    def remove(cls, agent_id: str) -> bool:
        """Remove agent by ID"""
        if agent_id in cls._instances:
            agent = cls._instances.pop(agent_id)
            logger.info(f"Agent removed: {agent.name}")
            return True
        return False

    @classmethod
    def clear(cls) -> None:
        """Clear all agent instances"""
        cls._instances.clear()
        logger.info("All agents cleared")


# Register default agent types on import
def _register_defaults():
    """Register default agent types"""
    from .base_agent import SimpleAgent

    AgentFactory.register(AgentType.SIMPLE, SimpleAgent)

    try:
        from .specialized.researcher_agent import ResearcherAgent
        AgentFactory.register(AgentType.RESEARCHER, ResearcherAgent)
    except ImportError:
        pass

    try:
        from .specialized.coder_agent import CoderAgent
        AgentFactory.register(AgentType.CODER, CoderAgent)
    except ImportError:
        pass

    try:
        from .specialized.writer_agent import WriterAgent
        AgentFactory.register(AgentType.WRITER, WriterAgent)
    except ImportError:
        pass

    try:
        from .specialized.analyst_agent import AnalystAgent
        AgentFactory.register(AgentType.ANALYST, AnalystAgent)
    except ImportError:
        pass


# Auto-register on module import
_register_defaults()

