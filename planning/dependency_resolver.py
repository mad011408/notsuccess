"""
NEXUS AI Agent - Dependency Resolver
"""

from typing import List, Dict, Set, Any
from dataclasses import dataclass

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class DependencyNode:
    """A node in dependency graph"""
    id: str
    dependencies: List[str]
    data: Any = None


class DependencyResolver:
    """
    Resolves dependencies between tasks

    Features:
    - Topological sorting
    - Cycle detection
    - Parallel group identification
    """

    def __init__(self):
        self._nodes: Dict[str, DependencyNode] = {}

    def add_node(self, node_id: str, dependencies: List[str], data: Any = None) -> None:
        """Add a dependency node"""
        self._nodes[node_id] = DependencyNode(
            id=node_id,
            dependencies=dependencies,
            data=data
        )

    def resolve(self) -> List[str]:
        """
        Resolve dependencies and return execution order

        Returns:
            List of node IDs in execution order
        """
        # Kahn's algorithm for topological sort
        in_degree: Dict[str, int] = {node_id: 0 for node_id in self._nodes}
        graph: Dict[str, List[str]] = {node_id: [] for node_id in self._nodes}

        for node_id, node in self._nodes.items():
            for dep in node.dependencies:
                if dep in graph:
                    graph[dep].append(node_id)
                    in_degree[node_id] += 1

        # Find nodes with no dependencies
        queue = [n for n, d in in_degree.items() if d == 0]
        result = []

        while queue:
            # Sort by id for deterministic order
            queue.sort()
            node_id = queue.pop(0)
            result.append(node_id)

            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._nodes):
            raise ValueError("Circular dependency detected")

        return result

    def get_parallel_groups(self) -> List[List[str]]:
        """
        Get groups of nodes that can run in parallel

        Returns:
            List of groups, each group can run in parallel
        """
        execution_order = self.resolve()
        groups: List[List[str]] = []
        current_group: List[str] = []
        completed: Set[str] = set()

        for node_id in execution_order:
            node = self._nodes[node_id]

            # Check if all dependencies are in previous groups
            deps_satisfied = all(
                dep in completed or dep not in self._nodes
                for dep in node.dependencies
            )

            if deps_satisfied:
                current_group.append(node_id)
            else:
                if current_group:
                    groups.append(current_group)
                    completed.update(current_group)
                current_group = [node_id]

        if current_group:
            groups.append(current_group)

        return groups

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in dependency graph

        Returns:
            List of cycles found (each cycle is a list of node IDs)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            node = self._nodes.get(node_id)
            if node:
                for dep in node.dependencies:
                    if dep not in visited:
                        cycle = dfs(dep)
                        if cycle:
                            return cycle
                    elif dep in rec_stack:
                        # Found cycle
                        cycle_start = path.index(dep)
                        return path[cycle_start:]

            path.pop()
            rec_stack.remove(node_id)
            return None

        for node_id in self._nodes:
            if node_id not in visited:
                cycle = dfs(node_id)
                if cycle:
                    cycles.append(cycle)

        return cycles

    def get_dependencies(self, node_id: str, recursive: bool = False) -> Set[str]:
        """
        Get dependencies of a node

        Args:
            node_id: Node to get dependencies for
            recursive: Include transitive dependencies

        Returns:
            Set of dependency IDs
        """
        node = self._nodes.get(node_id)
        if not node:
            return set()

        deps = set(node.dependencies)

        if recursive:
            to_process = list(deps)
            while to_process:
                dep_id = to_process.pop()
                dep_node = self._nodes.get(dep_id)
                if dep_node:
                    for sub_dep in dep_node.dependencies:
                        if sub_dep not in deps:
                            deps.add(sub_dep)
                            to_process.append(sub_dep)

        return deps

    def get_dependents(self, node_id: str) -> Set[str]:
        """
        Get nodes that depend on this node

        Args:
            node_id: Node to find dependents for

        Returns:
            Set of dependent node IDs
        """
        dependents = set()
        for nid, node in self._nodes.items():
            if node_id in node.dependencies:
                dependents.add(nid)
        return dependents

    def clear(self) -> None:
        """Clear all nodes"""
        self._nodes.clear()
