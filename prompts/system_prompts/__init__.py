"""NEXUS AI Agent - System Prompts - A2Z Connected"""

# Base System Prompts - Only from base_system_prompts.py
from .base_system_prompts import (
    DEFAULT_SYSTEM_PROMPT,
    ANALYST_SYSTEM_PROMPT,
    ASSISTANT_SYSTEM_PROMPT
)

# Specialized Coder Prompts
from .coder_prompts import (
    PYTHON_CODER,
    JAVASCRIPT_CODER,
    FULLSTACK_CODER
)

# CODER_SYSTEM_PROMPT - alias to PYTHON_CODER for backward compatibility
CODER_SYSTEM_PROMPT = PYTHON_CODER

# Specialized Researcher Prompts
from .researcher_prompts import (
    ACADEMIC_RESEARCHER,
    MARKET_RESEARCHER,
    TECHNICAL_RESEARCHER
)

# RESEARCHER_SYSTEM_PROMPT - alias to ACADEMIC_RESEARCHER for backward compatibility
RESEARCHER_SYSTEM_PROMPT = ACADEMIC_RESEARCHER

# Specialized Analyst Prompts
from .analyst_prompts import (
    DATA_ANALYST,
    BUSINESS_ANALYST,
    FINANCIAL_ANALYST
)

# Specialized Assistant Prompts
from .assistant_prompts import (
    GENERAL_ASSISTANT,
    WRITING_ASSISTANT,
    PLANNING_ASSISTANT
)

# All prompts mapping for easy access
SYSTEM_PROMPTS = {
    # Base prompts - default is DEFAULT_SYSTEM_PROMPT from base_system_prompts.py
    "default": DEFAULT_SYSTEM_PROMPT,
    "coder": CODER_SYSTEM_PROMPT,
    "researcher": RESEARCHER_SYSTEM_PROMPT,
    "analyst": ANALYST_SYSTEM_PROMPT,
    "assistant": ASSISTANT_SYSTEM_PROMPT,
    # Specialized coder
    "python_coder": PYTHON_CODER,
    "javascript_coder": JAVASCRIPT_CODER,
    "fullstack_coder": FULLSTACK_CODER,
    # Specialized researcher
    "academic_researcher": ACADEMIC_RESEARCHER,
    "market_researcher": MARKET_RESEARCHER,
    "technical_researcher": TECHNICAL_RESEARCHER,
    # Specialized analyst
    "data_analyst": DATA_ANALYST,
    "business_analyst": BUSINESS_ANALYST,
    "financial_analyst": FINANCIAL_ANALYST,
    # Specialized assistant
    "general_assistant": GENERAL_ASSISTANT,
    "writing_assistant": WRITING_ASSISTANT,
    "planning_assistant": PLANNING_ASSISTANT,
}


def get_system_prompt(prompt_type: str = "default") -> str:
    """Get system prompt by type - No filtering, direct pass"""
    return SYSTEM_PROMPTS.get(prompt_type.lower(), DEFAULT_SYSTEM_PROMPT)


def get_combined_prompt(*prompt_types: str) -> str:
    """
    Combine multiple prompts into one - Direct, no filtering

    Usage: get_combined_prompt("default", "coder", "researcher")
    This will combine all 3 prompts into one mega prompt
    """
    combined = []
    for ptype in prompt_types:
        prompt = SYSTEM_PROMPTS.get(ptype.lower())
        if prompt:
            combined.append(prompt)
    return "\n\n".join(combined) if combined else DEFAULT_SYSTEM_PROMPT


__all__ = [
    # Base
    "DEFAULT_SYSTEM_PROMPT",
    "CODER_SYSTEM_PROMPT",
    "RESEARCHER_SYSTEM_PROMPT",
    "ANALYST_SYSTEM_PROMPT",
    "ASSISTANT_SYSTEM_PROMPT",
    # Coder
    "PYTHON_CODER",
    "JAVASCRIPT_CODER",
    "FULLSTACK_CODER",
    # Researcher
    "ACADEMIC_RESEARCHER",
    "MARKET_RESEARCHER",
    "TECHNICAL_RESEARCHER",
    # Analyst
    "DATA_ANALYST",
    "BUSINESS_ANALYST",
    "FINANCIAL_ANALYST",
    # Assistant
    "GENERAL_ASSISTANT",
    "WRITING_ASSISTANT",
    "PLANNING_ASSISTANT",
    # Utilities
    "SYSTEM_PROMPTS",
    "get_system_prompt",
    "get_combined_prompt",
]
