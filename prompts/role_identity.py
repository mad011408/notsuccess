"""
NEXUS AI Agent - Role Identity System
Helper functions for identity creation - YOUR system prompt defines the actual identity
"""

from typing import Optional


def create_role_identity(
    character_name: str = "",
    character_description: str = "",
    behavioral_rules: str = "",
    response_style: str = "",
    knowledge_base: str = "",
    restrictions: str = ""
) -> str:
    """
    Create role identity string.
    YOUR system prompt in base_system_prompts.py defines the actual identity.
    This is just a helper if you need to create additional identity strings.
    """
    return ""


def create_assistant_backstory(
    name: str = "",
    creator: str = "",
    purpose: str = "",
    personality_traits: list = None,
    expertise_areas: list = None,
    communication_style: str = ""
) -> str:
    """Helper function - YOUR system prompt defines the actual backstory."""
    return ""


def create_perspective_anchor(
    perspective_name: str = "",
    worldview: str = "",
    values: list = None,
    response_framework: str = ""
) -> str:
    """Helper function - YOUR system prompt defines the actual perspective."""
    return ""


def create_conversational_persona(
    persona_name: str = "",
    tone: str = "",
    vocabulary_style: str = "",
    typical_phrases: list = None,
    response_patterns: str = ""
) -> str:
    """Helper function - YOUR system prompt defines the actual persona."""
    return ""


# Empty - YOUR system prompt in base_system_prompts.py is the actual identity
NEXUS_IDENTITY = ""


__all__ = [
    "create_role_identity",
    "create_assistant_backstory",
    "create_perspective_anchor",
    "create_conversational_persona",
    "NEXUS_IDENTITY"
]
