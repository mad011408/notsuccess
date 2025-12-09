"""NEXUS AI Agent - Processing Pipeline"""

from typing import Optional, List, Dict, Any, Callable, AsyncGenerator
from dataclasses import dataclass
import asyncio

from .base_pipeline import BasePipeline, PipelineResult, StepStatus, StepResult, PipelineStep
from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ProcessingConfig:
    """Processing pipeline configuration"""
    max_workers: int = 4
    timeout: float = 300.0
    retry_count: int = 3
    buffer_size: int = 100


class ProcessingPipeline(BasePipeline):
    """
    Advanced processing pipeline

    Features:
    - Async processing
    - Worker pools
    - Streaming support
    - Backpressure handling
    """

    def __init__(
        self,
        name: str = "ProcessingPipeline",
        config: Optional[ProcessingConfig] = None
    ):
        super().__init__(name)
        self.config = config or ProcessingConfig()
        self._queue: asyncio.Queue = None
        self._workers: List[asyncio.Task] = []
        self._running = False

    async def run(self, input_data: Any = None) -> PipelineResult:
        """Execute processing pipeline"""
        import time
        start_time = time.time()

        result = PipelineResult(success=True)
        current_data = input_data

        await self._trigger("on_start", input_data)

        try:
            for step in self._steps:
                await self._trigger("on_step_start", step.name)

                step_result = await step.execute(current_data, self._context)
                result.steps.append(step_result)

                await self._trigger("on_step_complete", step_result)

                if step_result.status == StepStatus.FAILED:
                    result.success = False
                    result.error = step_result.error
                    break

                current_data = step_result.output

            result.output = current_data

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            result.success = False
            result.error = str(e)

        result.total_duration = time.time() - start_time
        await self._trigger("on_complete", result)

        return result

    async def run_stream(
        self,
        input_stream: AsyncGenerator[Any, None]
    ) -> AsyncGenerator[Any, None]:
        """Process streaming input"""
        async for item in input_stream:
            result = await self.run(item)
            if result.success:
                yield result.output

    async def run_parallel(
        self,
        items: List[Any],
        max_concurrent: Optional[int] = None
    ) -> List[PipelineResult]:
        """Run pipeline on items in parallel"""
        max_concurrent = max_concurrent or self.config.max_workers
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_item(item):
            async with semaphore:
                return await self.run(item)

        tasks = [process_item(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def start_workers(self) -> None:
        """Start worker pool"""
        if self._running:
            return

        self._running = True
        self._queue = asyncio.Queue(maxsize=self.config.buffer_size)

        for i in range(self.config.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)

        logger.info(f"Started {self.config.max_workers} workers")

    async def stop_workers(self) -> None:
        """Stop worker pool"""
        self._running = False

        # Signal workers to stop
        for _ in self._workers:
            await self._queue.put(None)

        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        logger.info("Workers stopped")

    async def submit(self, item: Any) -> None:
        """Submit item to worker pool"""
        if not self._running:
            raise RuntimeError("Workers not started")

        await self._queue.put(item)

    async def _worker(self, name: str) -> None:
        """Worker coroutine"""
        while self._running:
            try:
                item = await self._queue.get()

                if item is None:
                    break

                result = await self.run(item)

                if not result.success:
                    logger.warning(f"{name}: Processing failed - {result.error}")

                self._queue.task_done()

            except Exception as e:
                logger.error(f"{name}: Worker error - {e}")

    def branch(
        self,
        condition: Callable[[Any], bool],
        true_steps: List[PipelineStep],
        false_steps: Optional[List[PipelineStep]] = None
    ) -> "ProcessingPipeline":
        """Add branching logic"""
        async def branch_step(data, context):
            steps_to_run = true_steps if condition(data) else (false_steps or [])
            current = data

            for step in steps_to_run:
                result = await step.execute(current, context)
                if result.status == StepStatus.FAILED:
                    raise RuntimeError(f"Branch step failed: {result.error}")
                current = result.output

            return current

        self.add_step("branch", branch_step)
        return self

    def parallel_steps(self, steps: List[PipelineStep]) -> "ProcessingPipeline":
        """Add steps that run in parallel"""
        async def parallel_step(data, context):
            tasks = [step.execute(data, context) for step in steps]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            outputs = []
            for result in results:
                if isinstance(result, Exception):
                    raise result
                if result.status == StepStatus.FAILED:
                    raise RuntimeError(f"Parallel step failed: {result.error}")
                outputs.append(result.output)

            return outputs

        self.add_step("parallel", parallel_step)
        return self

    def retry(
        self,
        step_name: str,
        max_retries: int = 3,
        backoff: float = 1.0
    ) -> "ProcessingPipeline":
        """Add retry wrapper to step"""
        for step in self._steps:
            if step.name == step_name:
                original_func = step.func

                async def retry_wrapper(data, context):
                    last_error = None
                    for attempt in range(max_retries):
                        try:
                            if asyncio.iscoroutinefunction(original_func):
                                return await original_func(data, context)
                            return original_func(data, context)
                        except Exception as e:
                            last_error = e
                            await asyncio.sleep(backoff * (attempt + 1))

                    raise last_error

                step.func = retry_wrapper
                break

        return self

    def checkpoint(self, name: str, save_func: Callable[[Any], None]) -> "ProcessingPipeline":
        """Add checkpoint to save intermediate results"""
        async def checkpoint_step(data, context):
            save_func(data)
            return data

        self.add_step(f"checkpoint_{name}", checkpoint_step)
        return self

