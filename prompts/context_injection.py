"""
NEXUS AI Agent - Context Injection System
Helper functions - YOUR system prompt in base_system_prompts.py is the actual context
"""

from typing import List, Dict, Any, Optional


def create_few_shot_examples(
    examples: List[Dict[str, str]] = None,
    instruction: str = ""
) -> str:
    """Helper function - YOUR system prompt defines actual examples."""
    return ""


def create_context_primer(
    situation: str = "",
    role: str = "",
    objective: str = "",
    constraints: List[str] = None
) -> str:
    """Helper function - YOUR system prompt defines the actual context."""
    return ""


def inject_behavioral_examples(
    behavior_type: str = "",
    positive_examples: List[str] = None,
    negative_examples: List[str] = None
) -> str:
    """Helper function - YOUR system prompt defines actual behaviors."""
    return ""


def create_conversation_memory(
    key_facts: List[str] = None,
    established_behaviors: List[str] = None,
    conversation_rules: List[str] = None
) -> str:
    """Helper function - YOUR system prompt defines the actual memory."""
    return ""


def create_response_template(
    template_name: str = "",
    structure: str = "",
    required_elements: List[str] = None,
    optional_elements: List[str] = None,
    example_response: str = ""
) -> str:
    """Helper function - YOUR system prompt defines actual templates."""
    return ""


def create_chain_of_thought_guide(
    thinking_steps: List[str] = None,
    reasoning_style: str = ""
) -> str:
    """Helper function - YOUR system prompt defines actual thinking process."""
    return ""


# Empty - YOUR system prompt in base_system_prompts.py is the actual context
NEXUS_CONTEXT_INJECTION = ""


__all__ = [
    "create_few_shot_examples",
    "create_context_primer",
    "inject_behavioral_examples",
    "create_conversation_memory",
    "create_response_template",
    "create_chain_of_thought_guide",
    "NEXUS_CONTEXT_INJECTION"
]
