"""
NEXUS AI Agent - Task Planner
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class PlanStep:
    """A step in a plan"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: Optional[float] = None
    priority: int = 0
    tools_required: List[str] = field(default_factory=list)
    status: str = "pending"


@dataclass
class Plan:
    """A complete plan"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskPlanner:
    """
    Creates execution plans for tasks

    Features:
    - Task decomposition
    - Step sequencing
    - Resource planning
    """

    def __init__(self):
        self._llm_call: Optional[Callable] = None

    def set_llm_call(self, llm_call: Callable) -> None:
        """Set LLM call function"""
        self._llm_call = llm_call

    async def create_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List[str]] = None
    ) -> Plan:
        """
        Create a plan for achieving a goal

        Args:
            goal: The goal to achieve
            context: Additional context
            available_tools: List of available tools

        Returns:
            Plan object
        """
        if not self._llm_call:
            raise ValueError("LLM call function not set")

        prompt = self._build_planning_prompt(goal, context, available_tools)
        response = await self._llm_call(prompt)

        steps = self._parse_plan(response)

        return Plan(
            goal=goal,
            steps=steps,
            metadata={
                "context": context,
                "available_tools": available_tools
            }
        )

    def _build_planning_prompt(
        self,
        goal: str,
        context: Optional[Dict[str, Any]],
        tools: Optional[List[str]]
    ) -> str:
        """Build planning prompt"""
        tools_str = ", ".join(tools) if tools else "general tools"
        context_str = f"\nContext: {context}\n" if context else ""

        return f"""Create a detailed plan to achieve this goal:

Goal: {goal}
{context_str}
Available tools: {tools_str}

Break down into specific steps:
1. [Step name]: [Description] (Dependencies: none, Tools: [tools needed])
2. [Step name]: [Description] (Dependencies: step 1, Tools: [tools needed])
...

Be specific and actionable."""

    def _parse_plan(self, response: str) -> List[PlanStep]:
        """Parse plan from LLM response"""
        steps = []
        lines = response.split("\n")

        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and "." in line[:3]:
                step = self._parse_step(line)
                if step:
                    steps.append(step)

        return steps

    def _parse_step(self, line: str) -> Optional[PlanStep]:
        """Parse a single step"""
        try:
            # Remove step number
            content = line.split(".", 1)[1].strip()

            # Parse name and description
            if ":" in content:
                name, rest = content.split(":", 1)
            else:
                name = content[:50]
                rest = content

            # Extract dependencies
            dependencies = []
            if "Dependencies:" in rest or "depends on" in rest.lower():
                dep_part = rest.lower().split("dependencies:")[-1] if "dependencies:" in rest.lower() else ""
                if dep_part:
                    deps = dep_part.split(",")
                    for d in deps:
                        d = d.strip()
                        if d and d != "none":
                            dependencies.append(d)

            # Extract tools
            tools = []
            if "Tools:" in rest:
                tools_part = rest.split("Tools:")[-1]
                tools = [t.strip() for t in tools_part.split(",")]

            return PlanStep(
                name=name.strip(),
                description=rest.strip(),
                dependencies=dependencies,
                tools_required=tools
            )

        except Exception as e:
            logger.error(f"Error parsing step: {e}")
            return None

    def validate_plan(self, plan: Plan) -> Dict[str, Any]:
        """Validate a plan"""
        issues = []

        # Check for circular dependencies
        if self._has_circular_deps(plan.steps):
            issues.append("Circular dependencies detected")

        # Check for missing dependencies
        step_ids = {s.id for s in plan.steps}
        for step in plan.steps:
            for dep in step.dependencies:
                if dep not in step_ids and dep != "none":
                    issues.append(f"Missing dependency: {dep}")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def _has_circular_deps(self, steps: List[PlanStep]) -> bool:
        """Check for circular dependencies"""
        # Simple cycle detection
        visited = set()
        rec_stack = set()

        def dfs(step_id):
            visited.add(step_id)
            rec_stack.add(step_id)

            step = next((s for s in steps if s.id == step_id), None)
            if step:
                for dep in step.dependencies:
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(step_id)
            return False

        for step in steps:
            if step.id not in visited:
                if dfs(step.id):
                    return True

        return False
