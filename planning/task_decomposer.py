"""
NEXUS AI Agent - Task Decomposer
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class SubTask:
    """A sub-task in decomposition"""
    id: int
    description: str
    complexity: str = "medium"  # low, medium, high
    estimated_tokens: int = 0
    parent_id: Optional[int] = None
    subtasks: List["SubTask"] = field(default_factory=list)


@dataclass
class DecompositionResult:
    """Result of task decomposition"""
    original_task: str
    subtasks: List[SubTask]
    total_subtasks: int
    max_depth: int


class TaskDecomposer:
    """
    Decomposes complex tasks into subtasks

    Features:
    - Hierarchical decomposition
    - Complexity estimation
    - Recursive breakdown
    """

    def __init__(self, max_depth: int = 3, min_subtasks: int = 2):
        self.max_depth = max_depth
        self.min_subtasks = min_subtasks
        self._llm_call: Optional[Callable] = None
        self._task_counter = 0

    def set_llm_call(self, llm_call: Callable) -> None:
        """Set LLM call function"""
        self._llm_call = llm_call

    async def decompose(
        self,
        task: str,
        depth: int = 0,
        context: Optional[Dict[str, Any]] = None
    ) -> DecompositionResult:
        """
        Decompose a task into subtasks

        Args:
            task: The task to decompose
            depth: Current depth in hierarchy
            context: Additional context

        Returns:
            DecompositionResult
        """
        if not self._llm_call:
            raise ValueError("LLM call function not set")

        self._task_counter = 0

        subtasks = await self._decompose_recursive(task, depth, context)

        return DecompositionResult(
            original_task=task,
            subtasks=subtasks,
            total_subtasks=self._count_subtasks(subtasks),
            max_depth=self._get_max_depth(subtasks)
        )

    async def _decompose_recursive(
        self,
        task: str,
        depth: int,
        context: Optional[Dict[str, Any]],
        parent_id: Optional[int] = None
    ) -> List[SubTask]:
        """Recursively decompose task"""
        if depth >= self.max_depth:
            return []

        prompt = self._build_decomposition_prompt(task, context)
        response = await self._llm_call(prompt)

        subtasks = self._parse_subtasks(response, parent_id)

        # Recursively decompose complex subtasks
        for subtask in subtasks:
            if subtask.complexity == "high" and depth < self.max_depth - 1:
                subtask.subtasks = await self._decompose_recursive(
                    subtask.description,
                    depth + 1,
                    context,
                    subtask.id
                )

        return subtasks

    def _build_decomposition_prompt(
        self,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build decomposition prompt"""
        context_str = f"\nContext: {context}\n" if context else ""

        return f"""Break down this task into smaller, actionable subtasks:

Task: {task}
{context_str}
List {self.min_subtasks}-5 subtasks:
1. [Subtask description] (Complexity: low/medium/high)
2. [Subtask description] (Complexity: low/medium/high)
...

Be specific and ensure subtasks are actionable."""

    def _parse_subtasks(
        self,
        response: str,
        parent_id: Optional[int]
    ) -> List[SubTask]:
        """Parse subtasks from response"""
        subtasks = []
        lines = response.split("\n")

        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and "." in line[:3]:
                subtask = self._parse_subtask(line, parent_id)
                if subtask:
                    subtasks.append(subtask)

        return subtasks

    def _parse_subtask(
        self,
        line: str,
        parent_id: Optional[int]
    ) -> Optional[SubTask]:
        """Parse a single subtask"""
        try:
            self._task_counter += 1

            # Remove number
            content = line.split(".", 1)[1].strip()

            # Extract complexity
            complexity = "medium"
            if "(Complexity:" in content or "(complexity:" in content:
                parts = content.lower().split("complexity:")
                if len(parts) > 1:
                    comp = parts[1].strip().rstrip(")").strip()
                    if comp in ["low", "medium", "high"]:
                        complexity = comp
                content = content.split("(")[0].strip()

            return SubTask(
                id=self._task_counter,
                description=content,
                complexity=complexity,
                parent_id=parent_id
            )

        except Exception as e:
            logger.error(f"Error parsing subtask: {e}")
            return None

    def _count_subtasks(self, subtasks: List[SubTask]) -> int:
        """Count total subtasks including nested"""
        count = len(subtasks)
        for subtask in subtasks:
            count += self._count_subtasks(subtask.subtasks)
        return count

    def _get_max_depth(self, subtasks: List[SubTask], current: int = 1) -> int:
        """Get maximum depth of subtask tree"""
        if not subtasks:
            return current - 1

        max_child_depth = current
        for subtask in subtasks:
            if subtask.subtasks:
                child_depth = self._get_max_depth(subtask.subtasks, current + 1)
                max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth

    def flatten(self, result: DecompositionResult) -> List[SubTask]:
        """Flatten hierarchical subtasks into list"""
        flat = []

        def collect(subtasks: List[SubTask]):
            for subtask in subtasks:
                flat.append(subtask)
                if subtask.subtasks:
                    collect(subtask.subtasks)

        collect(result.subtasks)
        return flat
