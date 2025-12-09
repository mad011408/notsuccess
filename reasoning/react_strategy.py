"""
NEXUS AI Agent - ReAct (Reasoning + Acting) Strategy
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from config.logging_config import get_logger


logger = get_logger(__name__)


class ActionType(str, Enum):
    """Types of actions"""
    SEARCH = "search"
    LOOKUP = "lookup"
    CALCULATE = "calculate"
    FINISH = "finish"


@dataclass
class ReActStep:
    """A step in ReAct loop"""
    step_number: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None


@dataclass
class ReActResult:
    """Result of ReAct reasoning"""
    query: str
    steps: List[ReActStep]
    final_answer: str
    success: bool
    iterations: int


class ReActStrategy:
    """
    ReAct Reasoning + Acting Strategy

    Interleaves reasoning with action execution.
    """

    def __init__(
        self,
        max_iterations: int = 10,
        tools: Optional[Dict[str, Callable]] = None
    ):
        self.max_iterations = max_iterations
        self.tools = tools or {}

    def register_tool(self, name: str, func: Callable, description: str = "") -> None:
        """Register a tool"""
        self.tools[name] = {"function": func, "description": description}

    async def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        llm_call: Optional[Callable] = None
    ) -> ReActResult:
        """
        Perform ReAct reasoning

        Args:
            query: Question to answer
            context: Additional context
            llm_call: Function to call LLM

        Returns:
            ReActResult with reasoning steps
        """
        if not llm_call:
            raise ValueError("llm_call function required")

        steps: List[ReActStep] = []
        iteration = 0
        scratchpad = ""

        while iteration < self.max_iterations:
            iteration += 1

            # Generate thought and action
            prompt = self._build_prompt(query, scratchpad, context)
            response = await llm_call(prompt)

            # Parse response
            step = self._parse_step(response, iteration)
            steps.append(step)

            # Check if finished
            if step.action and step.action.lower() == "finish":
                return ReActResult(
                    query=query,
                    steps=steps,
                    final_answer=step.action_input or step.thought,
                    success=True,
                    iterations=iteration
                )

            # Execute action
            if step.action:
                observation = await self._execute_action(
                    step.action,
                    step.action_input or ""
                )
                step.observation = observation

                # Update scratchpad
                scratchpad += f"\nThought {iteration}: {step.thought}"
                scratchpad += f"\nAction {iteration}: {step.action}[{step.action_input}]"
                scratchpad += f"\nObservation {iteration}: {observation}"

        # Max iterations reached
        return ReActResult(
            query=query,
            steps=steps,
            final_answer="Unable to find answer within iteration limit.",
            success=False,
            iterations=iteration
        )

    def _build_prompt(
        self,
        query: str,
        scratchpad: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build ReAct prompt"""
        tools_desc = "\n".join([
            f"  {name}: {info.get('description', 'No description')}"
            for name, info in self.tools.items()
        ])

        context_str = ""
        if context:
            context_str = f"\nContext: {context}\n"

        return f"""Answer the following question using the available tools.
{context_str}
Available tools:
{tools_desc}
  Finish[answer]: Return the final answer

Use the following format:

Thought: [your reasoning about what to do next]
Action: [the action to take, should be one of the tools]
Action Input: [the input to the action]

Observation will be provided after each action.

Question: {query}
{scratchpad}

Thought:"""

    def _parse_step(self, response: str, step_number: int) -> ReActStep:
        """Parse ReAct step from response"""
        thought = ""
        action = None
        action_input = None

        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line.lower().startswith("thought"):
                thought = line.split(":", 1)[1].strip() if ":" in line else line
            elif line.lower().startswith("action input"):
                action_input = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.lower().startswith("action"):
                action_part = line.split(":", 1)[1].strip() if ":" in line else line
                # Parse action[input] format
                if "[" in action_part and "]" in action_part:
                    action = action_part.split("[")[0].strip()
                    action_input = action_part.split("[")[1].rstrip("]")
                else:
                    action = action_part

        return ReActStep(
            step_number=step_number,
            thought=thought,
            action=action,
            action_input=action_input
        )

    async def _execute_action(self, action: str, action_input: str) -> str:
        """Execute an action"""
        action_lower = action.lower()

        if action_lower in self.tools:
            tool = self.tools[action_lower]
            func = tool["function"]
            try:
                if asyncio.iscoroutinefunction(func):
                    import asyncio
                    result = await func(action_input)
                else:
                    result = func(action_input)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        return f"Unknown action: {action}"

    def add_default_tools(self) -> None:
        """Add default tools"""
        # Search tool
        def search(query: str) -> str:
            return f"Search results for '{query}': [Results would be here]"

        # Lookup tool
        def lookup(term: str) -> str:
            return f"Definition of '{term}': [Definition would be here]"

        # Calculate tool
        def calculate(expression: str) -> str:
            try:
                result = eval(expression)
                return str(result)
            except:
                return "Error: Invalid expression"

        self.register_tool("Search", search, "Search for information")
        self.register_tool("Lookup", lookup, "Look up a term or concept")
        self.register_tool("Calculate", calculate, "Perform calculations")

    def format_trace(self, result: ReActResult) -> str:
        """Format reasoning trace for display"""
        lines = [f"Question: {result.query}\n"]

        for step in result.steps:
            lines.append(f"Thought {step.step_number}: {step.thought}")
            if step.action:
                lines.append(f"Action {step.step_number}: {step.action}[{step.action_input}]")
            if step.observation:
                lines.append(f"Observation {step.step_number}: {step.observation}")
            lines.append("")

        lines.append(f"Final Answer: {result.final_answer}")

        return "\n".join(lines)


import asyncio
