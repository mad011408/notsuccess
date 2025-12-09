"""NEXUS AI Agent - Data Pipeline"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

from .base_pipeline import BasePipeline, PipelineResult, StepStatus, StepResult
from config.logging_config import get_logger


logger = get_logger(__name__)


class DataPipeline(BasePipeline):
    """
    Pipeline for data processing workflows

    Features:
    - Data transformation steps
    - Validation
    - Error handling
    - Batch processing
    """

    def __init__(self, name: str = "DataPipeline"):
        super().__init__(name)
        self._validators: List[Callable] = []
        self._transformers: List[Callable] = []
        self._batch_size: int = 100

    async def run(self, input_data: Any = None) -> PipelineResult:
        """Execute data pipeline"""
        import time
        start_time = time.time()

        result = PipelineResult(success=True)
        current_data = input_data

        await self._trigger("on_start", input_data)

        try:
            # Validation phase
            for validator in self._validators:
                if not validator(current_data):
                    result.success = False
                    result.error = "Validation failed"
                    return result

            # Execute pipeline steps
            for step in self._steps:
                await self._trigger("on_step_start", step.name)

                step_result = await step.execute(current_data, self._context)
                result.steps.append(step_result)

                await self._trigger("on_step_complete", step_result)

                if step_result.status == StepStatus.FAILED:
                    result.success = False
                    result.error = step_result.error
                    break

                if step_result.status == StepStatus.COMPLETED:
                    current_data = step_result.output

            # Apply transformers
            for transformer in self._transformers:
                current_data = transformer(current_data)

            result.output = current_data

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            result.success = False
            result.error = str(e)

        result.total_duration = time.time() - start_time
        await self._trigger("on_complete", result)

        return result

    def add_validator(self, validator: Callable[[Any], bool]) -> "DataPipeline":
        """Add data validator"""
        self._validators.append(validator)
        return self

    def add_transformer(self, transformer: Callable[[Any], Any]) -> "DataPipeline":
        """Add data transformer"""
        self._transformers.append(transformer)
        return self

    def set_batch_size(self, size: int) -> "DataPipeline":
        """Set batch size for processing"""
        self._batch_size = size
        return self

    async def run_batch(
        self,
        items: List[Any],
        continue_on_error: bool = True
    ) -> List[PipelineResult]:
        """Run pipeline on batch of items"""
        results = []

        for i in range(0, len(items), self._batch_size):
            batch = items[i:i + self._batch_size]

            for item in batch:
                result = await self.run(item)
                results.append(result)

                if not result.success and not continue_on_error:
                    return results

        return results

    # Common data operations
    def filter(self, predicate: Callable[[Any], bool]) -> "DataPipeline":
        """Add filter step"""
        def filter_step(data, context):
            if isinstance(data, list):
                return [item for item in data if predicate(item)]
            return data if predicate(data) else None

        return self.add_step("filter", filter_step)

    def map(self, mapper: Callable[[Any], Any]) -> "DataPipeline":
        """Add map step"""
        def map_step(data, context):
            if isinstance(data, list):
                return [mapper(item) for item in data]
            return mapper(data)

        return self.add_step("map", map_step)

    def reduce(self, reducer: Callable, initial: Any = None) -> "DataPipeline":
        """Add reduce step"""
        def reduce_step(data, context):
            if not isinstance(data, list):
                return data

            from functools import reduce as functools_reduce
            if initial is not None:
                return functools_reduce(reducer, data, initial)
            return functools_reduce(reducer, data)

        return self.add_step("reduce", reduce_step)

    def flatten(self) -> "DataPipeline":
        """Add flatten step"""
        def flatten_step(data, context):
            if not isinstance(data, list):
                return data

            result = []
            for item in data:
                if isinstance(item, list):
                    result.extend(item)
                else:
                    result.append(item)
            return result

        return self.add_step("flatten", flatten_step)

    def unique(self, key: Optional[Callable] = None) -> "DataPipeline":
        """Add unique/dedup step"""
        def unique_step(data, context):
            if not isinstance(data, list):
                return data

            seen = set()
            result = []
            for item in data:
                k = key(item) if key else item
                if k not in seen:
                    seen.add(k)
                    result.append(item)
            return result

        return self.add_step("unique", unique_step)

    def sort(self, key: Optional[Callable] = None, reverse: bool = False) -> "DataPipeline":
        """Add sort step"""
        def sort_step(data, context):
            if not isinstance(data, list):
                return data
            return sorted(data, key=key, reverse=reverse)

        return self.add_step("sort", sort_step)

    def group_by(self, key: Callable) -> "DataPipeline":
        """Add group by step"""
        def group_step(data, context):
            if not isinstance(data, list):
                return data

            groups = {}
            for item in data:
                k = key(item)
                if k not in groups:
                    groups[k] = []
                groups[k].append(item)
            return groups

        return self.add_step("group_by", group_step)

