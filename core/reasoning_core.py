"""
NEXUS AI Agent - Reasoning Core
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

from config.logging_config import get_logger
from config.constants import ReasoningStrategy


logger = get_logger(__name__)


@dataclass
class ReasoningStep:
    """A single step in the reasoning process"""
    step_number: int
    thought: str
    conclusion: Optional[str] = None
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)


@dataclass
class ReasoningResult:
    """Result of a reasoning process"""
    strategy: ReasoningStrategy
    steps: List[ReasoningStep]
    final_answer: str
    confidence: float
    total_tokens: int = 0
    reasoning_path: str = ""


class ReasoningStrategy(ABC):
    """Abstract base class for reasoning strategies"""

    @abstractmethod
    async def reason(
        self,
        query: str,
        context: Dict[str, Any],
        llm_call: Callable
    ) -> ReasoningResult:
        """Execute reasoning strategy"""
        pass


class ChainOfThoughtReasoning(ReasoningStrategy):
    """Chain of Thought reasoning implementation"""

    async def reason(
        self,
        query: str,
        context: Dict[str, Any],
        llm_call: Callable
    ) -> ReasoningResult:
        """Execute Chain of Thought reasoning"""
        prompt = f"""Let's think through this step by step.

Question: {query}

Please provide your reasoning in numbered steps, then give your final answer.

Step 1:"""

        response = await llm_call(prompt)

        steps = self._parse_steps(response)
        final_answer = self._extract_final_answer(response)

        return ReasoningResult(
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
            steps=steps,
            final_answer=final_answer,
            confidence=self._calculate_confidence(steps),
            reasoning_path=response
        )

    def _parse_steps(self, response: str) -> List[ReasoningStep]:
        """Parse numbered steps from response"""
        steps = []
        lines = response.split("\n")
        current_step = None

        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and "." in line[:3]:
                if current_step:
                    steps.append(current_step)
                step_num = int(line.split(".")[0])
                thought = line.split(".", 1)[1].strip() if "." in line else line
                current_step = ReasoningStep(
                    step_number=step_num,
                    thought=thought
                )
            elif current_step and line:
                current_step.thought += " " + line

        if current_step:
            steps.append(current_step)

        return steps

    def _extract_final_answer(self, response: str) -> str:
        """Extract final answer from response"""
        markers = ["Therefore", "Thus", "In conclusion", "Final answer", "The answer is"]
        for marker in markers:
            if marker.lower() in response.lower():
                idx = response.lower().find(marker.lower())
                return response[idx:].strip()
        return response.split("\n")[-1].strip()

    def _calculate_confidence(self, steps: List[ReasoningStep]) -> float:
        """Calculate confidence based on reasoning steps"""
        if not steps:
            return 0.5
        # More steps with clear conclusions = higher confidence
        return min(0.9, 0.5 + (len(steps) * 0.1))


class TreeOfThoughtReasoning(ReasoningStrategy):
    """Tree of Thought reasoning implementation"""

    def __init__(self, num_branches: int = 3, max_depth: int = 3):
        self.num_branches = num_branches
        self.max_depth = max_depth

    async def reason(
        self,
        query: str,
        context: Dict[str, Any],
        llm_call: Callable
    ) -> ReasoningResult:
        """Execute Tree of Thought reasoning"""
        # Generate initial thoughts
        branches = await self._generate_branches(query, llm_call)

        # Evaluate branches
        evaluated = await self._evaluate_branches(branches, query, llm_call)

        # Select best path
        best_branch = max(evaluated, key=lambda x: x["score"])

        # Expand best branch
        final_answer = await self._expand_branch(best_branch, query, llm_call)

        steps = [
            ReasoningStep(
                step_number=i + 1,
                thought=b["thought"],
                confidence=b["score"]
            )
            for i, b in enumerate(evaluated)
        ]

        return ReasoningResult(
            strategy=ReasoningStrategy.TREE_OF_THOUGHT,
            steps=steps,
            final_answer=final_answer,
            confidence=best_branch["score"],
            reasoning_path=str(evaluated)
        )

    async def _generate_branches(
        self,
        query: str,
        llm_call: Callable
    ) -> List[Dict[str, Any]]:
        """Generate multiple thought branches"""
        prompt = f"""Given this question: {query}

Generate {self.num_branches} different approaches to solve this problem.
Format each approach as:
Approach 1: [description]
Approach 2: [description]
Approach 3: [description]"""

        response = await llm_call(prompt)
        branches = []

        for line in response.split("\n"):
            if line.strip().startswith("Approach"):
                thought = line.split(":", 1)[1].strip() if ":" in line else line
                branches.append({"thought": thought, "score": 0.0})

        return branches[:self.num_branches]

    async def _evaluate_branches(
        self,
        branches: List[Dict[str, Any]],
        query: str,
        llm_call: Callable
    ) -> List[Dict[str, Any]]:
        """Evaluate and score branches"""
        for branch in branches:
            prompt = f"""Evaluate this approach to solving: {query}

Approach: {branch['thought']}

Rate this approach from 0 to 1 based on:
- Likelihood of success
- Efficiency
- Completeness

Score (just the number):"""

            response = await llm_call(prompt)
            try:
                score = float(response.strip().split()[0])
                branch["score"] = min(1.0, max(0.0, score))
            except:
                branch["score"] = 0.5

        return branches

    async def _expand_branch(
        self,
        branch: Dict[str, Any],
        query: str,
        llm_call: Callable
    ) -> str:
        """Expand the best branch to get final answer"""
        prompt = f"""Using this approach: {branch['thought']}

Answer the question: {query}

Provide a complete and detailed answer:"""

        return await llm_call(prompt)


class ReActReasoning(ReasoningStrategy):
    """ReAct (Reasoning + Acting) strategy"""

    def __init__(self, tools: Dict[str, Callable] = None):
        self.tools = tools or {}

    async def reason(
        self,
        query: str,
        context: Dict[str, Any],
        llm_call: Callable
    ) -> ReasoningResult:
        """Execute ReAct reasoning loop"""
        steps = []
        max_iterations = 5
        iteration = 0

        current_context = query

        while iteration < max_iterations:
            # Generate thought and action
            prompt = self._build_react_prompt(current_context, steps)
            response = await llm_call(prompt)

            step = self._parse_react_step(response, iteration + 1)
            steps.append(step)

            if "Final Answer:" in response:
                final_answer = response.split("Final Answer:")[-1].strip()
                return ReasoningResult(
                    strategy=ReasoningStrategy.REACT,
                    steps=steps,
                    final_answer=final_answer,
                    confidence=0.8,
                    reasoning_path="\n".join([s.thought for s in steps])
                )

            # Execute action if specified
            if step.conclusion and step.conclusion in self.tools:
                observation = await self._execute_action(step.conclusion, {})
                current_context += f"\nObservation: {observation}"

            iteration += 1

        return ReasoningResult(
            strategy=ReasoningStrategy.REACT,
            steps=steps,
            final_answer="Could not reach conclusion within iteration limit.",
            confidence=0.3,
            reasoning_path="\n".join([s.thought for s in steps])
        )

    def _build_react_prompt(
        self,
        context: str,
        history: List[ReasoningStep]
    ) -> str:
        """Build ReAct prompt"""
        tools_desc = ", ".join(self.tools.keys()) if self.tools else "none"
        history_str = "\n".join([
            f"Thought {s.step_number}: {s.thought}"
            for s in history
        ])

        return f"""Question: {context}

Available tools: {tools_desc}

{history_str}

Think step by step:
Thought: [your reasoning]
Action: [tool to use or "Final Answer"]
Action Input: [input for tool]"""

    def _parse_react_step(self, response: str, step_num: int) -> ReasoningStep:
        """Parse ReAct response"""
        thought = ""
        action = None

        for line in response.split("\n"):
            if line.startswith("Thought:"):
                thought = line[8:].strip()
            elif line.startswith("Action:"):
                action = line[7:].strip()

        return ReasoningStep(
            step_number=step_num,
            thought=thought,
            conclusion=action
        )

    async def _execute_action(
        self,
        action: str,
        action_input: Dict[str, Any]
    ) -> str:
        """Execute an action/tool"""
        if action in self.tools:
            try:
                result = self.tools[action](**action_input)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        return f"Unknown action: {action}"


class ReasoningCore:
    """Main reasoning orchestrator"""

    def __init__(self):
        self._strategies: Dict[str, ReasoningStrategy] = {
            "cot": ChainOfThoughtReasoning(),
            "tot": TreeOfThoughtReasoning(),
            "react": ReActReasoning()
        }
        self._default_strategy = "cot"

    def register_strategy(self, name: str, strategy: ReasoningStrategy) -> None:
        """Register a reasoning strategy"""
        self._strategies[name] = strategy

    async def reason(
        self,
        query: str,
        context: Dict[str, Any],
        llm_call: Callable,
        strategy: Optional[str] = None
    ) -> ReasoningResult:
        """Execute reasoning with specified strategy"""
        strategy_name = strategy or self._default_strategy
        strategy_impl = self._strategies.get(strategy_name)

        if not strategy_impl:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        return await strategy_impl.reason(query, context, llm_call)

    def set_default_strategy(self, strategy: str) -> None:
        """Set default reasoning strategy"""
        if strategy in self._strategies:
            self._default_strategy = strategy
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
