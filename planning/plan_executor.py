"""
NEXUS AI Agent - Plan Executor
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from .task_planner import Plan, PlanStep

from config.logging_config import get_logger


logger = get_logger(__name__)


class StepStatus(str, Enum):
    """Status of a plan step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of executing a step"""
    step_id: str
    status: StepStatus
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0


@dataclass
class ExecutionResult:
    """Result of executing a plan"""
    plan_id: str
    success: bool
    step_results: List[StepResult]
    total_duration_ms: float
    steps_completed: int
    steps_failed: int


class PlanExecutor:
    """
    Executes plans step by step

    Features:
    - Sequential and parallel execution
    - Error handling and recovery
    - Progress tracking
    """

    def __init__(self, max_parallel: int = 3):
        self.max_parallel = max_parallel
        self._step_handlers: Dict[str, Callable] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            "on_step_start": [],
            "on_step_complete": [],
            "on_step_error": [],
            "on_plan_complete": []
        }

    def register_handler(self, step_type: str, handler: Callable) -> None:
        """Register a handler for a step type"""
        self._step_handlers[step_type] = handler

    def add_callback(self, event: str, callback: Callable) -> None:
        """Add callback for event"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    async def execute(
        self,
        plan: Plan,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute a plan

        Args:
            plan: The plan to execute
            context: Execution context

        Returns:
            ExecutionResult
        """
        start_time = datetime.utcnow()
        step_results: List[StepResult] = []
        completed_steps: set = set()

        # Build dependency graph
        ready_steps = self._get_ready_steps(plan.steps, completed_steps)

        while ready_steps:
            # Execute ready steps (potentially in parallel)
            batch_results = await self._execute_batch(ready_steps, context)
            step_results.extend(batch_results)

            # Update completed steps
            for result in batch_results:
                if result.status == StepStatus.COMPLETED:
                    completed_steps.add(result.step_id)

            # Get next batch of ready steps
            ready_steps = self._get_ready_steps(plan.steps, completed_steps)

            # Check for stuck execution
            if not ready_steps and len(completed_steps) < len(plan.steps):
                # Some steps couldn't be executed
                break

        end_time = datetime.utcnow()
        total_duration = (end_time - start_time).total_seconds() * 1000

        completed = sum(1 for r in step_results if r.status == StepStatus.COMPLETED)
        failed = sum(1 for r in step_results if r.status == StepStatus.FAILED)

        result = ExecutionResult(
            plan_id=plan.id,
            success=failed == 0,
            step_results=step_results,
            total_duration_ms=total_duration,
            steps_completed=completed,
            steps_failed=failed
        )

        await self._trigger("on_plan_complete", result)

        return result

    def _get_ready_steps(
        self,
        steps: List[PlanStep],
        completed: set
    ) -> List[PlanStep]:
        """Get steps ready to execute"""
        ready = []
        for step in steps:
            if step.id in completed:
                continue
            if step.status == "completed":
                continue

            # Check if all dependencies are satisfied
            deps_satisfied = all(
                dep in completed or dep == "none"
                for dep in step.dependencies
            )

            if deps_satisfied:
                ready.append(step)

        return ready

    async def _execute_batch(
        self,
        steps: List[PlanStep],
        context: Optional[Dict[str, Any]]
    ) -> List[StepResult]:
        """Execute a batch of steps"""
        # Limit parallelism
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_semaphore(step):
            async with semaphore:
                return await self._execute_step(step, context)

        tasks = [execute_with_semaphore(step) for step in steps]
        return await asyncio.gather(*tasks)

    async def _execute_step(
        self,
        step: PlanStep,
        context: Optional[Dict[str, Any]]
    ) -> StepResult:
        """Execute a single step"""
        result = StepResult(
            step_id=step.id,
            status=StepStatus.RUNNING,
            started_at=datetime.utcnow()
        )

        await self._trigger("on_step_start", step)

        try:
            # Find handler
            handler = None
            for tool in step.tools_required:
                if tool in self._step_handlers:
                    handler = self._step_handlers[tool]
                    break

            if handler:
                if asyncio.iscoroutinefunction(handler):
                    output = await handler(step, context)
                else:
                    output = handler(step, context)
                result.output = output
                result.status = StepStatus.COMPLETED
            else:
                # No handler - simulate completion
                result.output = f"Step '{step.name}' completed (no handler)"
                result.status = StepStatus.COMPLETED

            await self._trigger("on_step_complete", step, result)

        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            logger.error(f"Step {step.id} failed: {e}")
            await self._trigger("on_step_error", step, e)

        finally:
            result.completed_at = datetime.utcnow()
            if result.started_at:
                result.duration_ms = (
                    result.completed_at - result.started_at
                ).total_seconds() * 1000

        return result

    async def _trigger(self, event: str, *args) -> None:
        """Trigger callbacks"""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                logger.error(f"Callback error: {e}")
