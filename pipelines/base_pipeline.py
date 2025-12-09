"""NEXUS AI Agent - Base Pipeline"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Callable, Generic, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from config.logging_config import get_logger


logger = get_logger(__name__)


T = TypeVar('T')


class StepStatus(str, Enum):
    """Pipeline step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of a pipeline step"""
    step_name: str
    status: StepStatus
    output: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    success: bool
    steps: List[StepResult] = field(default_factory=list)
    output: Any = None
    total_duration: float = 0.0
    error: Optional[str] = None


class PipelineStep:
    """Single step in a pipeline"""

    def __init__(
        self,
        name: str,
        func: Callable,
        description: str = "",
        retry_count: int = 0,
        timeout: Optional[float] = None,
        condition: Optional[Callable] = None
    ):
        self.name = name
        self.func = func
        self.description = description
        self.retry_count = retry_count
        self.timeout = timeout
        self.condition = condition

    async def execute(self, input_data: Any, context: Dict[str, Any]) -> StepResult:
        """Execute the step"""
        import time
        start_time = time.time()

        # Check condition
        if self.condition and not self.condition(input_data, context):
            return StepResult(
                step_name=self.name,
                status=StepStatus.SKIPPED,
                duration=0.0
            )

        attempts = 0
        last_error = None

        while attempts <= self.retry_count:
            try:
                # Execute with timeout if specified
                if asyncio.iscoroutinefunction(self.func):
                    if self.timeout:
                        output = await asyncio.wait_for(
                            self.func(input_data, context),
                            timeout=self.timeout
                        )
                    else:
                        output = await self.func(input_data, context)
                else:
                    output = self.func(input_data, context)

                return StepResult(
                    step_name=self.name,
                    status=StepStatus.COMPLETED,
                    output=output,
                    duration=time.time() - start_time
                )

            except asyncio.TimeoutError:
                last_error = "Step timed out"
                attempts += 1

            except Exception as e:
                last_error = str(e)
                attempts += 1
                logger.warning(f"Step {self.name} failed (attempt {attempts}): {e}")

        return StepResult(
            step_name=self.name,
            status=StepStatus.FAILED,
            error=last_error,
            duration=time.time() - start_time
        )


class BasePipeline(ABC):
    """Base pipeline class"""

    def __init__(self, name: str = "Pipeline"):
        self.name = name
        self._steps: List[PipelineStep] = []
        self._context: Dict[str, Any] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            "on_start": [],
            "on_step_start": [],
            "on_step_complete": [],
            "on_complete": [],
            "on_error": [],
        }

    def add_step(
        self,
        name: str,
        func: Callable,
        description: str = "",
        retry_count: int = 0,
        timeout: Optional[float] = None,
        condition: Optional[Callable] = None
    ) -> "BasePipeline":
        """Add step to pipeline"""
        step = PipelineStep(
            name=name,
            func=func,
            description=description,
            retry_count=retry_count,
            timeout=timeout,
            condition=condition
        )
        self._steps.append(step)
        return self

    def remove_step(self, name: str) -> bool:
        """Remove step by name"""
        for i, step in enumerate(self._steps):
            if step.name == name:
                self._steps.pop(i)
                return True
        return False

    @abstractmethod
    async def run(self, input_data: Any = None) -> PipelineResult:
        """Execute the pipeline"""
        pass

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

    def on(self, event: str, callback: Callable) -> None:
        """Register callback"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def set_context(self, key: str, value: Any) -> None:
        """Set context value"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value"""
        return self._context.get(key, default)

    def clear_context(self) -> None:
        """Clear context"""
        self._context.clear()

    def get_steps(self) -> List[Dict[str, Any]]:
        """Get step information"""
        return [
            {
                "name": step.name,
                "description": step.description,
                "has_condition": step.condition is not None,
                "timeout": step.timeout,
                "retry_count": step.retry_count
            }
            for step in self._steps
        ]


class SequentialPipeline(BasePipeline):
    """Pipeline that executes steps sequentially"""

    async def run(self, input_data: Any = None) -> PipelineResult:
        """Execute steps sequentially"""
        import time
        start_time = time.time()

        result = PipelineResult(success=True)
        current_data = input_data

        await self._trigger("on_start", input_data)

        for step in self._steps:
            await self._trigger("on_step_start", step.name)

            step_result = await step.execute(current_data, self._context)
            result.steps.append(step_result)

            await self._trigger("on_step_complete", step_result)

            if step_result.status == StepStatus.FAILED:
                result.success = False
                result.error = f"Step '{step.name}' failed: {step_result.error}"
                await self._trigger("on_error", result.error)
                break

            if step_result.status == StepStatus.COMPLETED:
                current_data = step_result.output

        result.output = current_data
        result.total_duration = time.time() - start_time

        await self._trigger("on_complete", result)

        return result


class ParallelPipeline(BasePipeline):
    """Pipeline that executes steps in parallel"""

    async def run(self, input_data: Any = None) -> PipelineResult:
        """Execute steps in parallel"""
        import time
        start_time = time.time()

        await self._trigger("on_start", input_data)

        # Execute all steps concurrently
        tasks = [
            step.execute(input_data, self._context)
            for step in self._steps
        ]

        step_results = await asyncio.gather(*tasks, return_exceptions=True)

        result = PipelineResult(success=True)

        for i, step_result in enumerate(step_results):
            if isinstance(step_result, Exception):
                result.steps.append(StepResult(
                    step_name=self._steps[i].name,
                    status=StepStatus.FAILED,
                    error=str(step_result)
                ))
                result.success = False
            else:
                result.steps.append(step_result)
                if step_result.status == StepStatus.FAILED:
                    result.success = False

        # Combine outputs
        result.output = [
            s.output for s in result.steps
            if s.status == StepStatus.COMPLETED
        ]

        result.total_duration = time.time() - start_time

        await self._trigger("on_complete", result)

        return result

