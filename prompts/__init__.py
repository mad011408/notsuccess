"""NEXUS AI Agent - Prompts Module"""
from .prompt_manager import PromptManager
from .prompt_builder import PromptBuilder
from .prompt_template import PromptTemplate

# Direct pass-through - YOUR system prompt goes directly to model
from .prompt_enforcer import (
    enforce_system_prompt,
    add_user_message_reminder,
    build_master_prompt,
    create_response_primer,
    add_contextual_anchors_to_messages,
    # Empty placeholders for compatibility
    NEXUS_IDENTITY,
    NEXUS_CONTEXT_INJECTION,
    NEXUS_BEHAVIORAL_ANCHORS,
    NEXUS_ANTI_MANIPULATION,
    NEXUS_CONVERSATION_FRAME,
    NEXUS_HELPFUL_FRAMING,
    NEXUS_REALITY_GROUNDING,
)

__all__ = [
    "PromptManager",
    "PromptBuilder",
    "PromptTemplate",
    "enforce_system_prompt",
    "add_user_message_reminder",
    "build_master_prompt",
    "create_response_primer",
    "add_contextual_anchors_to_messages",
    "NEXUS_IDENTITY",
    "NEXUS_CONTEXT_INJECTION",
    "NEXUS_BEHAVIORAL_ANCHORS",
    "NEXUS_ANTI_MANIPULATION",
    "NEXUS_CONVERSATION_FRAME",
    "NEXUS_HELPFUL_FRAMING",
    "NEXUS_REALITY_GROUNDING",
]
