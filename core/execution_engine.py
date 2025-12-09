"""
NEXUS AI Agent - Execution Engine
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import traceback

from config.logging_config import get_logger
from config.constants import TaskStatus


logger = get_logger(__name__)


class ExecutionMode(str, Enum):
    """Execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    REACTIVE = "reactive"


@dataclass
class ExecutionStep:
    """A single execution step"""
    step_number: int
    action: str
    action_input: Dict[str, Any]
    result: Any = None
    error: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0


@dataclass
class ExecutionResult:
    """Result of an execution"""
    success: bool
    output: Any
    steps: List[ExecutionStep]
    total_duration_ms: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionEngine:
    """
    Handles task execution

    Manages:
    - Action execution
    - Tool invocation
    - Error handling
    - Retry logic
    """

    def __init__(
        self,
        max_retries: int = 3,
        timeout: int = 300,
        mode: ExecutionMode = ExecutionMode.REACTIVE
    ):
        self._max_retries = max_retries
        self._timeout = timeout
        self._mode = mode
        self._tools: Dict[str, Callable] = {}
        self._execution_history: List[ExecutionResult] = []

    def register_tool(self, name: str, tool: Callable) -> None:
        """Register a tool for execution"""
        self._tools[name] = tool
        logger.debug(f"Tool registered: {name}")

    def register_tools(self, tools: Dict[str, Callable]) -> None:
        """Register multiple tools"""
        self._tools.update(tools)

    async def execute(
        self,
        task: str,
        brain: Any,
        tools: Optional[List[str]] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Execute a task using available tools

        Args:
            task: Task description
            brain: Brain engine for LLM calls
            tools: List of tool names to use
            max_iterations: Maximum iterations

        Returns:
            Execution result dictionary
        """
        start_time = datetime.utcnow()
        steps: List[ExecutionStep] = []
        iteration = 0

        available_tools = {
            name: tool
            for name, tool in self._tools.items()
            if tools is None or name in tools
        }

        try:
            while iteration < max_iterations:
                # Get next action from brain
                action_info = await self._get_next_action(
                    brain, task, steps, available_tools
                )

                if action_info.get("done"):
                    # Task completed
                    result = ExecutionResult(
                        success=True,
                        output=action_info.get("output"),
                        steps=steps,
                        total_duration_ms=self._calculate_duration(start_time)
                    )
                    self._execution_history.append(result)
                    return self._result_to_dict(result)

                # Execute action
                step = await self._execute_action(
                    action_info.get("action"),
                    action_info.get("action_input", {}),
                    iteration + 1
                )
                steps.append(step)

                if step.status == TaskStatus.FAILED:
                    # Check if should retry
                    if not self._should_retry(step):
                        result = ExecutionResult(
                            success=False,
                            output=None,
                            steps=steps,
                            total_duration_ms=self._calculate_duration(start_time),
                            error=step.error
                        )
                        self._execution_history.append(result)
                        return self._result_to_dict(result)

                iteration += 1

            # Max iterations reached
            result = ExecutionResult(
                success=False,
                output=None,
                steps=steps,
                total_duration_ms=self._calculate_duration(start_time),
                error="Maximum iterations reached"
            )
            self._execution_history.append(result)
            return self._result_to_dict(result)

        except asyncio.TimeoutError:
            result = ExecutionResult(
                success=False,
                output=None,
                steps=steps,
                total_duration_ms=self._calculate_duration(start_time),
                error="Execution timeout"
            )
            self._execution_history.append(result)
            return self._result_to_dict(result)

        except Exception as e:
            logger.error(f"Execution error: {e}")
            result = ExecutionResult(
                success=False,
                output=None,
                steps=steps,
                total_duration_ms=self._calculate_duration(start_time),
                error=str(e)
            )
            self._execution_history.append(result)
            return self._result_to_dict(result)

    async def _get_next_action(
        self,
        brain: Any,
        task: str,
        history: List[ExecutionStep],
        tools: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """Get next action from brain"""
        # Build context with history
        history_str = "\n".join([
            f"Step {s.step_number}: {s.action} -> {s.result}"
            for s in history
        ])

        tools_desc = "\n".join([
            f"- {name}: Available for use"
            for name in tools.keys()
        ])

        prompt = f"""Task: {task}

Available tools:
{tools_desc}

Previous steps:
{history_str}

What should be the next action? If the task is complete, respond with:
DONE: [final output]

Otherwise respond with:
ACTION: [tool name]
INPUT: [input as JSON]"""

        # This would call brain's LLM
        # For now, return done after first iteration
        if not history:
            return {
                "action": list(tools.keys())[0] if tools else None,
                "action_input": {"task": task}
            }
        return {"done": True, "output": "Task completed"}

    async def _execute_action(
        self,
        action: str,
        action_input: Dict[str, Any],
        step_number: int
    ) -> ExecutionStep:
        """Execute a single action"""
        step = ExecutionStep(
            step_number=step_number,
            action=action,
            action_input=action_input,
            started_at=datetime.utcnow()
        )

        if action not in self._tools:
            step.status = TaskStatus.FAILED
            step.error = f"Unknown action: {action}"
            step.completed_at = datetime.utcnow()
            return step

        tool = self._tools[action]

        try:
            step.status = TaskStatus.IN_PROGRESS

            # Execute with retry
            for attempt in range(self._max_retries):
                try:
                    if asyncio.iscoroutinefunction(tool):
                        result = await asyncio.wait_for(
                            tool(**action_input),
                            timeout=self._timeout
                        )
                    else:
                        result = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: tool(**action_input)
                        )

                    step.result = result
                    step.status = TaskStatus.COMPLETED
                    break

                except Exception as e:
                    if attempt == self._max_retries - 1:
                        raise
                    logger.warning(f"Retry {attempt + 1} for {action}: {e}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        except asyncio.TimeoutError:
            step.status = TaskStatus.FAILED
            step.error = f"Timeout executing {action}"

        except Exception as e:
            step.status = TaskStatus.FAILED
            step.error = str(e)
            logger.error(f"Error executing {action}: {e}\n{traceback.format_exc()}")

        finally:
            step.completed_at = datetime.utcnow()
            if step.started_at:
                step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000

        return step

    def _should_retry(self, step: ExecutionStep) -> bool:
        """Determine if step should be retried"""
        if not step.error:
            return False

        # Retryable errors
        retryable = ["timeout", "rate_limit", "connection", "temporary"]
        error_lower = step.error.lower()
        return any(r in error_lower for r in retryable)

    def _calculate_duration(self, start_time: datetime) -> float:
        """Calculate duration in milliseconds"""
        return (datetime.utcnow() - start_time).total_seconds() * 1000

    def _result_to_dict(self, result: ExecutionResult) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "total_duration_ms": result.total_duration_ms,
            "steps": [
                {
                    "step_number": s.step_number,
                    "action": s.action,
                    "action_input": s.action_input,
                    "result": str(s.result)[:500] if s.result else None,
                    "error": s.error,
                    "status": s.status.value,
                    "duration_ms": s.duration_ms
                }
                for s in result.steps
            ]
        }

    async def execute_action(
        self,
        action: str,
        action_input: Dict[str, Any]
    ) -> Any:
        """Execute a single action directly"""
        if action not in self._tools:
            raise ValueError(f"Unknown action: {action}")

        tool = self._tools[action]

        if asyncio.iscoroutinefunction(tool):
            return await tool(**action_input)
        else:
            return tool(**action_input)

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history"""
        return [self._result_to_dict(r) for r in self._execution_history]

    def clear_history(self) -> None:
        """Clear execution history"""
        self._execution_history = []

    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self._tools.keys())
