"""
NEXUS AI Agent - Tree of Thought Reasoning
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
import asyncio

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ThoughtNode:
    """A node in the thought tree"""
    id: str
    thought: str
    parent_id: Optional[str] = None
    children: List["ThoughtNode"] = field(default_factory=list)
    score: float = 0.0
    depth: int = 0
    is_solution: bool = False


@dataclass
class TreeOfThoughtResult:
    """Result of ToT reasoning"""
    query: str
    root: ThoughtNode
    best_path: List[ThoughtNode]
    final_answer: str
    confidence: float
    total_nodes: int


class TreeOfThought:
    """
    Tree of Thought Reasoning Strategy

    Explores multiple reasoning paths and evaluates them.
    """

    def __init__(
        self,
        num_branches: int = 3,
        max_depth: int = 3,
        beam_width: int = 2
    ):
        self.num_branches = num_branches
        self.max_depth = max_depth
        self.beam_width = beam_width
        self._node_counter = 0

    async def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        llm_call: Optional[Callable] = None
    ) -> TreeOfThoughtResult:
        """
        Perform tree of thought reasoning

        Args:
            query: Question to answer
            context: Additional context
            llm_call: Function to call LLM

        Returns:
            TreeOfThoughtResult with reasoning tree
        """
        if not llm_call:
            raise ValueError("llm_call function required")

        self._node_counter = 0

        # Create root node
        root = ThoughtNode(
            id=self._get_node_id(),
            thought=query,
            depth=0
        )

        # Build tree using BFS with beam search
        await self._expand_tree(root, llm_call, context)

        # Find best path
        best_path = self._find_best_path(root)

        # Generate final answer from best path
        final_answer = await self._generate_answer(best_path, llm_call)

        return TreeOfThoughtResult(
            query=query,
            root=root,
            best_path=best_path,
            final_answer=final_answer,
            confidence=best_path[-1].score if best_path else 0.5,
            total_nodes=self._node_counter
        )

    async def _expand_tree(
        self,
        root: ThoughtNode,
        llm_call: Callable,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Expand tree using beam search"""
        current_level = [root]

        for depth in range(self.max_depth):
            next_level = []

            for node in current_level:
                # Generate child thoughts
                children = await self._generate_children(
                    node, llm_call, context
                )

                # Evaluate children
                for child in children:
                    child.score = await self._evaluate_thought(
                        child, llm_call, context
                    )

                node.children = children
                next_level.extend(children)

            # Beam search: keep top-k nodes
            next_level.sort(key=lambda x: x.score, reverse=True)
            current_level = next_level[:self.beam_width]

            if not current_level:
                break

    async def _generate_children(
        self,
        node: ThoughtNode,
        llm_call: Callable,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ThoughtNode]:
        """Generate child thoughts for a node"""
        prompt = f"""Given this thought process:
{self._get_path_to_node(node)}

Generate {self.num_branches} different next steps or approaches.
Format each as:
Approach 1: [description]
Approach 2: [description]
Approach 3: [description]"""

        response = await llm_call(prompt)

        children = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("Approach"):
                thought = line.split(":", 1)[1].strip() if ":" in line else line
                children.append(ThoughtNode(
                    id=self._get_node_id(),
                    thought=thought,
                    parent_id=node.id,
                    depth=node.depth + 1
                ))

        return children[:self.num_branches]

    async def _evaluate_thought(
        self,
        node: ThoughtNode,
        llm_call: Callable,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Evaluate a thought node"""
        path = self._get_path_to_node(node)

        prompt = f"""Evaluate this reasoning path on a scale of 0 to 1:

{path}

Consider:
- Does it make logical sense?
- Is it making progress toward a solution?
- Is it avoiding errors or contradictions?

Score (just the number between 0 and 1):"""

        response = await llm_call(prompt)

        try:
            score = float(response.strip().split()[0])
            return min(1.0, max(0.0, score))
        except:
            return 0.5

    def _find_best_path(self, root: ThoughtNode) -> List[ThoughtNode]:
        """Find the highest-scoring path"""
        best_path = []
        best_score = -1

        def dfs(node: ThoughtNode, path: List[ThoughtNode]):
            nonlocal best_path, best_score

            current_path = path + [node]

            if not node.children:
                # Leaf node
                path_score = sum(n.score for n in current_path) / len(current_path)
                if path_score > best_score:
                    best_score = path_score
                    best_path = current_path
            else:
                for child in node.children:
                    dfs(child, current_path)

        dfs(root, [])
        return best_path

    async def _generate_answer(
        self,
        path: List[ThoughtNode],
        llm_call: Callable
    ) -> str:
        """Generate final answer from best path"""
        if not path:
            return "Unable to generate answer"

        reasoning = "\n".join([
            f"Step {i + 1}: {node.thought}"
            for i, node in enumerate(path)
        ])

        prompt = f"""Based on this reasoning:

{reasoning}

Provide a clear, concise final answer:"""

        return await llm_call(prompt)

    def _get_path_to_node(self, node: ThoughtNode) -> str:
        """Get reasoning path to a node"""
        path = []
        current = node

        while current:
            path.insert(0, current.thought)
            # Find parent
            current = None  # Would need to track this properly

        return "\n-> ".join(path) if path else node.thought

    def _get_node_id(self) -> str:
        """Generate unique node ID"""
        self._node_counter += 1
        return f"node_{self._node_counter}"

    def visualize_tree(self, root: ThoughtNode, indent: int = 0) -> str:
        """Create text visualization of tree"""
        lines = []
        prefix = "  " * indent

        score_str = f" (score: {root.score:.2f})" if root.score > 0 else ""
        lines.append(f"{prefix}└─ {root.thought[:50]}...{score_str}")

        for child in root.children:
            lines.append(self.visualize_tree(child, indent + 1))

        return "\n".join(lines)
