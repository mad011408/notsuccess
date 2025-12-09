"""NEXUS AI Agent - Custom Tool Builder"""
from typing import Callable, Dict, Any, List, Optional
from .tool_registry import tool_registry

class CustomToolBuilder:
    """Builder for creating custom tools"""

    def __init__(self, name: str):
        self._name = name
        self._description = ""
        self._parameters: Dict[str, Dict[str, Any]] = {}
        self._handler: Optional[Callable] = None
        self._category = "custom"

    def description(self, desc: str) -> "CustomToolBuilder":
        self._description = desc
        return self

    def parameter(self, name: str, type: str = "string", description: str = "", required: bool = True) -> "CustomToolBuilder":
        self._parameters[name] = {"type": type, "description": description, "required": required}
        return self

    def handler(self, func: Callable) -> "CustomToolBuilder":
        self._handler = func
        return self

    def category(self, cat: str) -> "CustomToolBuilder":
        self._category = cat
        return self

    def build(self) -> None:
        if not self._handler:
            raise ValueError("Handler function required")
        tool_registry.register(self._name, self._handler, self._description, self._category)

def create_tool(name: str) -> CustomToolBuilder:
    return CustomToolBuilder(name)
