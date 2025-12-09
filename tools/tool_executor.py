"""
NEXUS AI Agent - Tool Executor
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio
import json

from .tool_registry import ToolRegistry, tool_registry
from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ToolResult:
    """Result of tool execution"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class ToolExecutor:
    """
    Executes tools safely

    Features:
    - Safe execution with error handling
    - Timeout management
    - Result formatting
    """

    def __init__(self, registry: Optional[ToolRegistry] = None, timeout: int = 30):
        self.registry = registry or tool_registry
        self.timeout = timeout

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute a tool

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            ToolResult
        """
        import time
        start_time = time.time()

        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Unknown tool: {tool_name}"
            )

        if not tool.enabled:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool disabled: {tool_name}"
            )

        try:
            # Parse arguments if string
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            # Execute with timeout
            if asyncio.iscoroutinefunction(tool.function):
                result = await asyncio.wait_for(
                    tool.function(**arguments),
                    timeout=self.timeout
                )
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: tool.function(**arguments)
                )

            execution_time = (time.time() - start_time) * 1000

            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time
            )

        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool timed out after {self.timeout}s"
            )
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e)
            )

    async def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[ToolResult]:
        """Execute multiple tool calls"""
        results = []
        for call in tool_calls:
            func = call.get("function", call)
            result = await self.execute(
                func.get("name"),
                func.get("arguments", {})
            )
            results.append(result)
        return results

    def format_result_for_llm(self, result: ToolResult) -> str:
        """Format result for LLM context"""
        if result.success:
            return json.dumps(result.result) if not isinstance(result.result, str) else result.result
        return f"Error: {result.error}"
