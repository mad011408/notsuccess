"""
NEXUS AI Agent - Advanced AI Agent Framework

A comprehensive framework for building intelligent AI agents with
multi-provider LLM support, advanced reasoning capabilities, and
extensive tool integration.
"""

__version__ = "1.0.0"
__author__ = "NEXUS AI"
__license__ = "MIT"

from .core.nexus_agent import NexusAgent, create_agent
from .config.settings import Settings, get_settings

__all__ = [
    "NexusAgent",
    "create_agent",
    "Settings",
    "get_settings",
    "__version__",
]

