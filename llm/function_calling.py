"""
NEXUS AI Agent - Function Calling Support
"""

from typing import Optional, List, Dict, Any, Callable, get_type_hints
from dataclasses import dataclass, field
import inspect
import json
import asyncio

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class FunctionParameter:
    """Function parameter definition"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


@dataclass
class FunctionDefinition:
    """Function definition for LLM"""
    name: str
    description: str
    parameters: List[FunctionParameter]
    handler: Optional[Callable] = None


@dataclass
class FunctionCall:
    """Represents a function call from LLM"""
    name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


@dataclass
class FunctionResult:
    """Result of a function execution"""
    name: str
    result: Any
    success: bool = True
    error: Optional[str] = None
    call_id: Optional[str] = None


class FunctionCaller:
    """
    Manages function calling for LLMs

    Features:
    - Function registration
    - Schema generation
    - Function execution
    - Result formatting
    """

    def __init__(self):
        self._functions: Dict[str, FunctionDefinition] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Register a function

        Args:
            func: Function to register
            name: Override function name
            description: Override description
        """
        func_name = name or func.__name__
        func_desc = description or func.__doc__ or f"Function {func_name}"

        # Extract parameters from function signature
        parameters = self._extract_parameters(func)

        definition = FunctionDefinition(
            name=func_name,
            description=func_desc,
            parameters=parameters,
            handler=func
        )

        self._functions[func_name] = definition
        self._handlers[func_name] = func

        logger.debug(f"Function registered: {func_name}")

    def register_from_dict(self, schema: Dict[str, Any], handler: Callable) -> None:
        """Register function from OpenAI-style schema"""
        name = schema.get("name", handler.__name__)

        parameters = []
        params_schema = schema.get("parameters", {})
        properties = params_schema.get("properties", {})
        required = params_schema.get("required", [])

        for param_name, param_info in properties.items():
            parameters.append(FunctionParameter(
                name=param_name,
                type=param_info.get("type", "string"),
                description=param_info.get("description", ""),
                required=param_name in required,
                enum=param_info.get("enum")
            ))

        definition = FunctionDefinition(
            name=name,
            description=schema.get("description", ""),
            parameters=parameters,
            handler=handler
        )

        self._functions[name] = definition
        self._handlers[name] = handler

    def _extract_parameters(self, func: Callable) -> List[FunctionParameter]:
        """Extract parameters from function signature"""
        parameters = []
        sig = inspect.signature(func)
        hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            param_type = hints.get(param_name, Any)
            type_str = self._python_type_to_json(param_type)

            has_default = param.default != inspect.Parameter.empty

            parameters.append(FunctionParameter(
                name=param_name,
                type=type_str,
                description=f"Parameter {param_name}",
                required=not has_default,
                default=param.default if has_default else None
            ))

        return parameters

    def _python_type_to_json(self, python_type: type) -> str:
        """Convert Python type to JSON schema type"""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        if hasattr(python_type, "__origin__"):
            return type_map.get(python_type.__origin__, "string")

        return type_map.get(python_type, "string")

    def get_schema(self, func_name: str) -> Optional[Dict[str, Any]]:
        """Get OpenAI-compatible function schema"""
        definition = self._functions.get(func_name)
        if not definition:
            return None

        properties = {}
        required = []

        for param in definition.parameters:
            prop = {"type": param.type, "description": param.description}
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "name": definition.name,
            "description": definition.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered functions"""
        return [
            self.get_schema(name)
            for name in self._functions
        ]

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get OpenAI tools-format schemas"""
        return [
            {"type": "function", "function": schema}
            for schema in self.get_all_schemas()
        ]

    async def execute(self, call: FunctionCall) -> FunctionResult:
        """
        Execute a function call

        Args:
            call: FunctionCall object

        Returns:
            FunctionResult with execution result
        """
        handler = self._handlers.get(call.name)

        if not handler:
            return FunctionResult(
                name=call.name,
                result=None,
                success=False,
                error=f"Unknown function: {call.name}",
                call_id=call.call_id
            )

        try:
            # Parse arguments if string
            args = call.arguments
            if isinstance(args, str):
                args = json.loads(args)

            # Execute function
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**args)
            else:
                result = handler(**args)

            return FunctionResult(
                name=call.name,
                result=result,
                success=True,
                call_id=call.call_id
            )

        except Exception as e:
            logger.error(f"Function execution error: {e}")
            return FunctionResult(
                name=call.name,
                result=None,
                success=False,
                error=str(e),
                call_id=call.call_id
            )

    async def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[FunctionResult]:
        """Execute multiple tool calls"""
        results = []

        for tc in tool_calls:
            func = tc.get("function", tc)
            call = FunctionCall(
                name=func.get("name"),
                arguments=func.get("arguments", {}),
                call_id=tc.get("id")
            )
            result = await self.execute(call)
            results.append(result)

        return results

    def parse_function_call(self, response: Dict[str, Any]) -> Optional[FunctionCall]:
        """Parse function call from LLM response"""
        # OpenAI format
        if "function_call" in response:
            fc = response["function_call"]
            return FunctionCall(
                name=fc.get("name"),
                arguments=json.loads(fc.get("arguments", "{}"))
            )

        # Tool calls format
        if "tool_calls" in response:
            tc = response["tool_calls"][0]
            func = tc.get("function", tc)
            return FunctionCall(
                name=func.get("name"),
                arguments=json.loads(func.get("arguments", "{}")),
                call_id=tc.get("id")
            )

        return None

    def format_result_for_llm(self, result: FunctionResult) -> Dict[str, str]:
        """Format result for LLM context"""
        content = json.dumps(result.result) if result.success else f"Error: {result.error}"

        return {
            "role": "tool",
            "tool_call_id": result.call_id or "",
            "content": content
        }

    def list_functions(self) -> List[str]:
        """List registered function names"""
        return list(self._functions.keys())

    def unregister(self, func_name: str) -> bool:
        """Unregister a function"""
        if func_name in self._functions:
            del self._functions[func_name]
            del self._handlers[func_name]
            return True
        return False

    def clear(self) -> None:
        """Clear all registered functions"""
        self._functions.clear()
        self._handlers.clear()


def function(name: Optional[str] = None, description: Optional[str] = None):
    """Decorator for registering functions"""
    def decorator(func: Callable) -> Callable:
        func._fc_name = name or func.__name__
        func._fc_description = description or func.__doc__
        return func
    return decorator
