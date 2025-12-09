"""
NEXUS AI Agent - Conversation Framing System
Helper functions - YOUR system prompt in base_system_prompts.py defines actual framing
"""

from typing import List, Dict, Any, Optional


def create_conversation_frame(
    frame_type: str = "",
    participants: Dict[str, str] = None,
    purpose: str = "",
    rules: List[str] = None,
    success_criteria: str = ""
) -> str:
    """Helper - YOUR system prompt defines actual frame."""
    return ""


def create_expectation_setting(
    what_user_can_expect: List[str] = None,
    what_assistant_will_do: List[str] = None,
    what_assistant_wont_do: List[str] = None
) -> str:
    """Helper - YOUR system prompt defines actual expectations."""
    return ""


def create_meta_instruction_frame(
    instruction_source: str = "",
    instruction_authority: str = "",
    instruction_permanence: str = ""
) -> str:
    """Helper - YOUR system prompt defines actual meta instructions."""
    return ""


def create_purpose_alignment(
    primary_purpose: str = "",
    secondary_purposes: List[str] = None,
    how_purpose_guides_behavior: str = ""
) -> str:
    """Helper - YOUR system prompt defines actual purpose."""
    return ""


def create_helpful_framing(
    definition_of_helpful: str = "",
    ways_to_be_helpful: List[str] = None,
    what_helpfulness_looks_like: str = ""
) -> str:
    """Helper - YOUR system prompt defines actual helpfulness."""
    return ""


def create_conversation_contract(
    my_commitments: List[str] = None,
    boundaries: List[str] = None,
    mutual_understanding: str = ""
) -> str:
    """Helper - YOUR system prompt defines actual contract."""
    return ""


def create_reality_grounding(
    what_is_real: List[str] = None,
    what_is_not_real: List[str] = None,
    how_to_handle_confusion: str = ""
) -> str:
    """Helper - YOUR system prompt defines actual reality."""
    return ""


# Empty - YOUR system prompt in base_system_prompts.py defines actual framing
NEXUS_CONVERSATION_FRAME = ""
NEXUS_HELPFUL_FRAMING = ""
NEXUS_REALITY_GROUNDING = ""


__all__ = [
    "create_conversation_frame",
    "create_expectation_setting",
    "create_meta_instruction_frame",
    "create_purpose_alignment",
    "create_helpful_framing",
    "create_conversation_contract",
    "create_reality_grounding",
    "NEXUS_CONVERSATION_FRAME",
    "NEXUS_HELPFUL_FRAMING",
    "NEXUS_REALITY_GROUNDING"
]
