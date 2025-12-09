"""NEXUS AI Agent - Agents Module"""

from .base_agent import BaseAgent, AgentCapability, AgentOutput
from .agent_factory import AgentFactory
from .multi_agent import MultiAgentSystem, AgentTeam

from .specialized import (
    ResearcherAgent,
    CoderAgent,
    WriterAgent,
    AnalystAgent,
)


__all__ = [
    "BaseAgent",
    "AgentCapability",
    "AgentOutput",
    "AgentFactory",
    "MultiAgentSystem",
    "AgentTeam",
    "ResearcherAgent",
    "CoderAgent",
    "WriterAgent",
    "AnalystAgent",
]

