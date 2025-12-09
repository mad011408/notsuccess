"""
NEXUS AI Agent - Tool Registry
"""

from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
import inspect

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a tool"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    enabled: bool = True


class ToolRegistry:
    """
    Central registry for all tools

    Features:
    - Tool registration
    - Tool discovery
    - Schema generation
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        function: Callable,
        description: str = "",
        category: str = "general"
    ) -> None:
        """Register a tool"""
        parameters = self._extract_parameters(function)

        self._tools[name] = ToolDefinition(
            name=name,
            description=description or function.__doc__ or f"Tool: {name}",
            function=function,
            parameters=parameters,
            category=category
        )

        logger.debug(f"Tool registered: {name}")

    def _extract_parameters(self, func: Callable) -> Dict[str, Any]:
        """Extract parameters from function signature"""
        sig = inspect.signature(func)
        params = {}

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            param_info = {
                "type": "string",
                "required": param.default == inspect.Parameter.empty
            }

            if param.annotation != inspect.Parameter.empty:
                type_map = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}
                param_info["type"] = type_map.get(param.annotation, "string")

            params[param_name] = param_info

        return params

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name"""
        return self._tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """List all tools"""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return [t for t in tools if t.enabled]

    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get OpenAI-compatible tool schema"""
        tool = self._tools.get(name)
        if not tool:
            return None

        properties = {}
        required = []

        for param_name, param_info in tool.parameters.items():
            properties[param_name] = {
                "type": param_info["type"],
                "description": f"Parameter: {param_name}"
            }
            if param_info.get("required"):
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all enabled tools"""
        return [self.get_schema(name) for name in self._tools if self._tools[name].enabled]

    def unregister(self, name: str) -> bool:
        """Unregister a tool"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def enable(self, name: str) -> bool:
        """Enable a tool"""
        if name in self._tools:
            self._tools[name].enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a tool"""
        if name in self._tools:
            self._tools[name].enabled = False
            return True
        return False


# Global registry
tool_registry = ToolRegistry()


def tool(name: Optional[str] = None, description: str = "", category: str = "general"):
    """Decorator for registering tools"""
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_registry.register(tool_name, func, description, category)
        return func
    return decorator
