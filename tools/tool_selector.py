"""
NEXUS AI Agent - Tool Selector
"""

from typing import Optional, List, Dict, Any, Callable

from .tool_registry import ToolRegistry, tool_registry, ToolDefinition
from config.logging_config import get_logger


logger = get_logger(__name__)


class ToolSelector:
    """
    Selects appropriate tools for tasks

    Features:
    - Keyword-based selection
    - LLM-based selection
    - Category filtering
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or tool_registry
        self._llm_call: Optional[Callable] = None

    def set_llm_call(self, llm_call: Callable) -> None:
        """Set LLM call function"""
        self._llm_call = llm_call

    def select_by_keywords(
        self,
        query: str,
        limit: int = 5
    ) -> List[ToolDefinition]:
        """Select tools by keyword matching"""
        query_lower = query.lower()
        scored = []

        for tool in self.registry.list_tools():
            score = 0
            name_lower = tool.name.lower()
            desc_lower = tool.description.lower()

            # Name matching
            if name_lower in query_lower:
                score += 3
            for word in query_lower.split():
                if word in name_lower:
                    score += 2
                if word in desc_lower:
                    score += 1

            if score > 0:
                scored.append((score, tool))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [tool for _, tool in scored[:limit]]

    async def select_with_llm(
        self,
        query: str,
        limit: int = 3
    ) -> List[ToolDefinition]:
        """Select tools using LLM"""
        if not self._llm_call:
            return self.select_by_keywords(query, limit)

        tools = self.registry.list_tools()
        tools_desc = "\n".join([
            f"- {t.name}: {t.description}"
            for t in tools
        ])

        prompt = f"""Given this task: {query}

Available tools:
{tools_desc}

Which tools would be most useful? List up to {limit} tool names, one per line:"""

        response = await self._llm_call(prompt)

        selected = []
        for line in response.split("\n"):
            line = line.strip().lstrip("- ").lower()
            for tool in tools:
                if tool.name.lower() in line:
                    selected.append(tool)
                    break

        return selected[:limit]

    def select_by_category(self, category: str) -> List[ToolDefinition]:
        """Select all tools in a category"""
        return self.registry.list_tools(category=category)

    def get_tool_for_action(self, action: str) -> Optional[ToolDefinition]:
        """Get a tool matching an action name"""
        action_lower = action.lower()
        for tool in self.registry.list_tools():
            if tool.name.lower() == action_lower:
                return tool
        return None
