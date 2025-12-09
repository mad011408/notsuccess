"""NEXUS AI Agent - Agent Pipeline"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
import asyncio

from .base_pipeline import BasePipeline, PipelineResult, StepStatus, StepResult
from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class AgentStep:
    """Step executed by an agent"""
    name: str
    agent: Any  # BaseAgent type
    task_template: str
    process_output: Optional[Callable] = None


@dataclass
class AgentPipelineConfig:
    """Agent pipeline configuration"""
    max_iterations: int = 10
    timeout: float = 300.0
    allow_parallel: bool = False


class AgentPipeline(BasePipeline):
    """
    Pipeline that orchestrates agents

    Features:
    - Agent-based execution
    - Task templating
    - Inter-agent communication
    - Result aggregation
    """

    def __init__(
        self,
        name: str = "AgentPipeline",
        config: Optional[AgentPipelineConfig] = None
    ):
        super().__init__(name)
        self.config = config or AgentPipelineConfig()
        self._agents: Dict[str, Any] = {}
        self._agent_steps: List[AgentStep] = []
        self._results_buffer: List[Any] = []

    def add_agent(self, name: str, agent: Any) -> "AgentPipeline":
        """Register an agent"""
        self._agents[name] = agent
        return self

    def add_agent_step(
        self,
        name: str,
        agent_name: str,
        task_template: str,
        process_output: Optional[Callable] = None
    ) -> "AgentPipeline":
        """Add agent execution step"""
        if agent_name not in self._agents:
            raise ValueError(f"Agent not found: {agent_name}")

        self._agent_steps.append(AgentStep(
            name=name,
            agent=self._agents[agent_name],
            task_template=task_template,
            process_output=process_output
        ))
        return self

    async def run(self, input_data: Any = None) -> PipelineResult:
        """Execute agent pipeline"""
        import time
        start_time = time.time()

        result = PipelineResult(success=True)
        current_data = input_data
        self._results_buffer.clear()

        await self._trigger("on_start", input_data)

        try:
            # Execute regular steps first
            for step in self._steps:
                step_result = await step.execute(current_data, self._context)
                result.steps.append(step_result)

                if step_result.status == StepStatus.FAILED:
                    result.success = False
                    result.error = step_result.error
                    return result

                current_data = step_result.output

            # Execute agent steps
            if self.config.allow_parallel:
                agent_results = await self._run_agents_parallel(current_data)
            else:
                agent_results = await self._run_agents_sequential(current_data)

            result.steps.extend(agent_results)

            # Check for failures
            for step_result in agent_results:
                if step_result.status == StepStatus.FAILED:
                    result.success = False
                    result.error = step_result.error
                    break

            # Aggregate outputs
            if result.success:
                result.output = self._aggregate_results()

        except Exception as e:
            logger.error(f"Agent pipeline error: {e}")
            result.success = False
            result.error = str(e)

        result.total_duration = time.time() - start_time
        await self._trigger("on_complete", result)

        return result

    async def _run_agents_sequential(self, input_data: Any) -> List[StepResult]:
        """Run agent steps sequentially"""
        results = []
        current_data = input_data

        for agent_step in self._agent_steps:
            await self._trigger("on_step_start", agent_step.name)

            step_result = await self._execute_agent_step(agent_step, current_data)
            results.append(step_result)
            self._results_buffer.append(step_result.output)

            await self._trigger("on_step_complete", step_result)

            if step_result.status == StepStatus.FAILED:
                break

            current_data = step_result.output

        return results

    async def _run_agents_parallel(self, input_data: Any) -> List[StepResult]:
        """Run agent steps in parallel"""
        tasks = [
            self._execute_agent_step(step, input_data)
            for step in self._agent_steps
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        step_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                step_results.append(StepResult(
                    step_name=self._agent_steps[i].name,
                    status=StepStatus.FAILED,
                    error=str(result)
                ))
            else:
                step_results.append(result)
                self._results_buffer.append(result.output)

        return step_results

    async def _execute_agent_step(
        self,
        agent_step: AgentStep,
        input_data: Any
    ) -> StepResult:
        """Execute a single agent step"""
        import time
        start_time = time.time()

        try:
            # Build task from template
            task = self._build_task(agent_step.task_template, input_data)

            # Run agent
            agent_output = await agent_step.agent.run(task)

            # Process output if handler provided
            output = agent_output.content
            if agent_step.process_output:
                output = agent_step.process_output(output)

            return StepResult(
                step_name=agent_step.name,
                status=StepStatus.COMPLETED if agent_output.success else StepStatus.FAILED,
                output=output,
                error=agent_output.error,
                duration=time.time() - start_time,
                metadata={"agent": agent_step.agent.name}
            )

        except Exception as e:
            return StepResult(
                step_name=agent_step.name,
                status=StepStatus.FAILED,
                error=str(e),
                duration=time.time() - start_time
            )

    def _build_task(self, template: str, data: Any) -> str:
        """Build task from template"""
        task = template

        # Replace placeholders
        if isinstance(data, dict):
            for key, value in data.items():
                task = task.replace(f"{{{key}}}", str(value))

        task = task.replace("{input}", str(data))
        task = task.replace("{context}", str(self._context))

        return task

    def _aggregate_results(self) -> Any:
        """Aggregate results from all agent steps"""
        if len(self._results_buffer) == 1:
            return self._results_buffer[0]
        return self._results_buffer

    def chain(
        self,
        agent_names: List[str],
        task_template: str
    ) -> "AgentPipeline":
        """Chain multiple agents"""
        for i, name in enumerate(agent_names):
            step_name = f"chain_{name}_{i}"
            self.add_agent_step(step_name, name, task_template)
        return self

    def fork(
        self,
        agent_names: List[str],
        task_template: str
    ) -> "AgentPipeline":
        """Fork execution to multiple agents"""
        old_parallel = self.config.allow_parallel
        self.config.allow_parallel = True

        for name in agent_names:
            step_name = f"fork_{name}"
            self.add_agent_step(step_name, name, task_template)

        self.config.allow_parallel = old_parallel
        return self

    def get_agents(self) -> List[str]:
        """Get registered agent names"""
        return list(self._agents.keys())

    def get_agent_steps(self) -> List[Dict[str, Any]]:
        """Get agent step information"""
        return [
            {
                "name": step.name,
                "agent": step.agent.name,
                "task_template": step.task_template[:100]
            }
            for step in self._agent_steps
        ]

