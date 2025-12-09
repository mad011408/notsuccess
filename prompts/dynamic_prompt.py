"""NEXUS AI Agent - Dynamic Prompt"""
from typing import Optional, Dict, Any, Callable

class DynamicPrompt:
    """Prompt that can be dynamically modified based on context"""

    def __init__(self, base_template: str):
        self.base_template = base_template
        self._modifiers: list = []

    def add_modifier(self, condition: Callable[[Dict[str, Any]], bool], modifier: str) -> "DynamicPrompt":
        """Add conditional modifier"""
        self._modifiers.append((condition, modifier))
        return self

    def build(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt with context"""
        context = context or {}
        prompt = self.base_template

        for condition, modifier in self._modifiers:
            if condition(context):
                prompt += f"\n{modifier}"

        # Variable substitution
        for key, value in context.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))

        return prompt
