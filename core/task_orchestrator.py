"""
NEXUS AI Agent - Task Orchestrator
"""

from typing import Optional, List, Dict, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid

from config.logging_config import get_logger
from config.constants import TaskStatus


logger = get_logger(__name__)


class TaskPriority(int, Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class Task:
    """Represents a task to be executed"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    subtasks: List["Task"] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if task is ready to execute"""
        return all(dep in completed_tasks for dep in self.dependencies)


@dataclass
class TaskPlan:
    """Execution plan for tasks"""
    tasks: List[Task]
    execution_order: List[str]
    parallel_groups: List[List[str]]
    estimated_duration: Optional[float] = None


class TaskOrchestrator:
    """
    Orchestrates task execution

    Handles:
    - Task scheduling
    - Dependency resolution
    - Parallel execution
    - Progress tracking
    """

    def __init__(self, max_concurrent: int = 5):
        self._tasks: Dict[str, Task] = {}
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._running: Set[str] = set()
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._callbacks: Dict[str, List[Callable]] = {
            "on_task_start": [],
            "on_task_complete": [],
            "on_task_fail": [],
            "on_all_complete": []
        }

    def add_task(self, task: Task) -> str:
        """Add a task to the orchestrator"""
        self._tasks[task.id] = task
        logger.info(f"Task added: {task.name} ({task.id})")
        return task.id

    def add_tasks(self, tasks: List[Task]) -> List[str]:
        """Add multiple tasks"""
        return [self.add_task(task) for task in tasks]

    def create_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[str]] = None
    ) -> Task:
        """Create and add a new task"""
        task = Task(
            name=name,
            description=description,
            priority=priority,
            dependencies=dependencies or []
        )
        self.add_task(task)
        return task

    def build_plan(self) -> TaskPlan:
        """Build execution plan based on dependencies"""
        # Topological sort for execution order
        execution_order = self._topological_sort()

        # Group tasks that can run in parallel
        parallel_groups = self._find_parallel_groups(execution_order)

        return TaskPlan(
            tasks=list(self._tasks.values()),
            execution_order=execution_order,
            parallel_groups=parallel_groups
        )

    def _topological_sort(self) -> List[str]:
        """Topological sort of tasks based on dependencies"""
        in_degree: Dict[str, int] = {tid: 0 for tid in self._tasks}
        graph: Dict[str, List[str]] = {tid: [] for tid in self._tasks}

        for task_id, task in self._tasks.items():
            for dep in task.dependencies:
                if dep in graph:
                    graph[dep].append(task_id)
                    in_degree[task_id] += 1

        # Find all tasks with no dependencies
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort by priority (higher first)
            queue.sort(key=lambda x: self._tasks[x].priority.value, reverse=True)
            task_id = queue.pop(0)
            result.append(task_id)

            for neighbor in graph[task_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._tasks):
            raise ValueError("Circular dependency detected in tasks")

        return result

    def _find_parallel_groups(self, execution_order: List[str]) -> List[List[str]]:
        """Find groups of tasks that can run in parallel"""
        groups: List[List[str]] = []
        current_group: List[str] = []
        current_deps: Set[str] = set()

        for task_id in execution_order:
            task = self._tasks[task_id]

            # Check if task can be added to current group
            if not any(dep in current_group for dep in task.dependencies):
                current_group.append(task_id)
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [task_id]

        if current_group:
            groups.append(current_group)

        return groups

    async def execute(
        self,
        executor: Callable[[Task], Any],
        plan: Optional[TaskPlan] = None
    ) -> Dict[str, Any]:
        """
        Execute all tasks

        Args:
            executor: Function to execute each task
            plan: Optional execution plan

        Returns:
            Results dictionary
        """
        if plan is None:
            plan = self.build_plan()

        results: Dict[str, Any] = {}

        for group in plan.parallel_groups:
            # Execute tasks in parallel within each group
            tasks_to_run = [
                self._execute_task(task_id, executor)
                for task_id in group
                if self._tasks[task_id].is_ready(self._completed)
            ]

            group_results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

            for task_id, result in zip(group, group_results):
                if isinstance(result, Exception):
                    self._tasks[task_id].error = str(result)
                    self._tasks[task_id].status = TaskStatus.FAILED
                    self._failed.add(task_id)
                    await self._trigger_callback("on_task_fail", self._tasks[task_id])
                else:
                    results[task_id] = result

        await self._trigger_callback("on_all_complete", results)

        return results

    async def _execute_task(
        self,
        task_id: str,
        executor: Callable[[Task], Any]
    ) -> Any:
        """Execute a single task"""
        async with self._semaphore:
            task = self._tasks[task_id]
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.utcnow()
            self._running.add(task_id)

            await self._trigger_callback("on_task_start", task)

            try:
                if asyncio.iscoroutinefunction(executor):
                    result = await executor(task)
                else:
                    result = executor(task)

                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                self._completed.add(task_id)
                self._running.discard(task_id)

                await self._trigger_callback("on_task_complete", task)

                return result

            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                self._failed.add(task_id)
                self._running.discard(task_id)
                raise

    def add_callback(self, event: str, callback: Callable) -> None:
        """Add callback for an event"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    async def _trigger_callback(self, event: str, *args, **kwargs) -> None:
        """Trigger callbacks for an event"""
        for callback in self._callbacks.get(event, []):
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            "total_tasks": len(self._tasks),
            "completed": len(self._completed),
            "failed": len(self._failed),
            "running": len(self._running),
            "pending": len(self._tasks) - len(self._completed) - len(self._failed) - len(self._running),
            "tasks": {
                tid: {
                    "name": task.name,
                    "status": task.status.value,
                    "priority": task.priority.value
                }
                for tid, task in self._tasks.items()
            }
        }

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self._tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        task = self._tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            return True
        return False

    def reset(self) -> None:
        """Reset orchestrator state"""
        self._tasks.clear()
        self._completed.clear()
        self._failed.clear()
        self._running.clear()
