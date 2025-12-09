"""
NEXUS AI Agent - Prompt Template
"""

from typing import Optional, List, Dict, Any
import re


class PromptTemplate:
    """
    Prompt template with variable substitution

    Usage:
        template = PromptTemplate("Hello, {name}!")
        prompt = template.format(name="World")
    """

    def __init__(self, template: str, variables: Optional[List[str]] = None):
        self.template = template
        self.variables = variables or self._extract_variables()

    def _extract_variables(self) -> List[str]:
        """Extract variable names from template"""
        return re.findall(r'\{(\w+)\}', self.template)

    def format(self, **kwargs) -> str:
        """Format template with variables"""
        result = self.template
        for var, value in kwargs.items():
            result = result.replace(f"{{{var}}}", str(value))
        return result

    def partial(self, **kwargs) -> "PromptTemplate":
        """Create partial template with some variables filled"""
        new_template = self.format(**kwargs)
        remaining_vars = [v for v in self.variables if v not in kwargs]
        return PromptTemplate(new_template, remaining_vars)

    def validate(self, **kwargs) -> bool:
        """Check if all variables are provided"""
        return all(var in kwargs for var in self.variables)

    def __str__(self) -> str:
        return self.template

    def __repr__(self) -> str:
        return f"PromptTemplate(variables={self.variables})"
