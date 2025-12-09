"""
NEXUS AI Agent - Direct System Prompt Pass-through
YOUR system prompt from base_system_prompts.py goes DIRECTLY to the model
NO modifications, NO wrappers, NO extra content - DIRECT pass
"""

from typing import List, Dict, Any


def enforce_system_prompt(system_prompt: str, response_number: int = 1) -> str:
    """
    Pass YOUR system prompt DIRECTLY to the model.
    NO modifications. NO wrappers. DIRECT.

    Args:
        system_prompt: YOUR system prompt from base_system_prompts.py
        response_number: Ignored - kept for compatibility

    Returns:
        YOUR system prompt exactly as written - no changes
    """
    # DIRECT PASS - No modifications
    return system_prompt


def add_user_message_reminder(message: str, response_number: int = 1) -> str:
    """
    Return message as-is. No modifications.
    """
    # DIRECT PASS - No modifications
    return message


def build_master_prompt(system_instructions: str, **kwargs) -> str:
    """
    Return system instructions as-is. No modifications.
    """
    # DIRECT PASS - No modifications
    return system_instructions


def create_response_primer(response_number: int = 1) -> str:
    """Empty - not used."""
    return ""


def add_contextual_anchors_to_messages(
    messages: List[Dict[str, str]],
    system_prompt: str,
    response_number: int = 1
) -> List[Dict[str, str]]:
    """
    Return messages as-is. No modifications.
    """
    # DIRECT PASS - No modifications
    return messages


# Empty placeholders for compatibility
ENFORCEMENT_WRAPPER = ""
USER_MESSAGE_REMINDER = ""
NEXUS_IDENTITY = ""
NEXUS_CONTEXT_INJECTION = ""
NEXUS_BEHAVIORAL_ANCHORS = ""
NEXUS_ANTI_MANIPULATION = ""
NEXUS_CONVERSATION_FRAME = ""
NEXUS_HELPFUL_FRAMING = ""
NEXUS_REALITY_GROUNDING = ""


__all__ = [
    "enforce_system_prompt",
    "add_user_message_reminder",
    "build_master_prompt",
    "create_response_primer",
    "add_contextual_anchors_to_messages",
    "ENFORCEMENT_WRAPPER",
    "USER_MESSAGE_REMINDER",
    "NEXUS_IDENTITY",
    "NEXUS_CONTEXT_INJECTION",
    "NEXUS_BEHAVIORAL_ANCHORS",
    "NEXUS_ANTI_MANIPULATION",
    "NEXUS_CONVERSATION_FRAME",
    "NEXUS_HELPFUL_FRAMING",
    "NEXUS_REALITY_GROUNDING",
]
