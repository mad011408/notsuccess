"""
NEXUS AI Agent - Central Brain Engine
"""

import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

from config.settings import Settings
from config.logging_config import get_logger
from config.constants import ReasoningStrategy, MessageRole
from prompts.system_prompts import DEFAULT_SYSTEM_PROMPT, get_system_prompt


logger = get_logger(__name__)


@dataclass
class ThoughtProcess:
    """Represents a thought in the reasoning process"""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    is_final: bool = False


@dataclass
class BrainContext:
    """Context for brain processing"""
    messages: List[Dict[str, str]]
    system_prompt: str = None  # Will default to DEFAULT_SYSTEM_PROMPT
    tools: List[Dict[str, Any]] = None
    temperature: float = 0.7
    max_tokens: int = 49000
    stop_sequences: Optional[List[str]] = None

    def __post_init__(self):
        # Ensure system_prompt is set - DIRECT CONNECTION
        if self.system_prompt is None:
            self.system_prompt = DEFAULT_SYSTEM_PROMPT
        if self.tools is None:
            self.tools = []


class BrainEngine:
    """
    Central Brain Engine - The cognitive core of NEXUS

    Handles:
    - LLM communication
    - Reasoning orchestration
    - Tool selection and execution
    - Response generation
    """

    def __init__(self, agent_config: Any, settings: Settings):
        self.config = agent_config
        self.settings = settings
        self._llm_client = None
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._reasoning_strategy = agent_config.reasoning_strategy
        self._thought_history: List[ThoughtProcess] = []
        # System prompt from config - Direct connection, no filtering
        self._system_prompt = getattr(agent_config, 'system_prompt', None) or DEFAULT_SYSTEM_PROMPT

    async def initialize(self) -> None:
        """Initialize LLM client"""
        from llm.llm_client import LLMClient
        self._llm_client = LLMClient(
            provider=self.config.provider,
            model=self.config.model,
            system_prompt=self._system_prompt  # DIRECT - pass system prompt
        )
        await self._llm_client.initialize()

    async def process(self, context: BrainContext) -> str:
        """
        Process input and generate response

        Args:
            context: Brain context with messages and configuration

        Returns:
            Generated response
        """
        if not self._llm_client:
            await self.initialize()

        # Apply reasoning strategy
        if self._reasoning_strategy == ReasoningStrategy.REACT:
            return await self._process_react(context)
        elif self._reasoning_strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            return await self._process_cot(context)
        else:
            return await self._process_direct(context)

    async def process_stream(
        self,
        context: BrainContext
    ) -> AsyncGenerator[str, None]:
        """
        Process input and stream response

        Args:
            context: Brain context

        Yields:
            Response chunks
        """
        if not self._llm_client:
            await self.initialize()

        async for chunk in self._llm_client.generate_stream(
            messages=context.messages,
            system=context.system_prompt,
            temperature=context.temperature,
            max_tokens=context.max_tokens
        ):
            yield chunk

    async def _process_direct(self, context: BrainContext) -> str:
        """Direct LLM call without reasoning"""
        response = await self._llm_client.generate(
            messages=context.messages,
            system=context.system_prompt,
            temperature=context.temperature,
            max_tokens=context.max_tokens
        )
        return response

    async def _process_cot(self, context: BrainContext) -> str:
        """Chain of Thought reasoning"""
        cot_prompt = self._build_cot_prompt(context)
        context.messages[-1]["content"] = cot_prompt

        response = await self._llm_client.generate(
            messages=context.messages,
            system=context.system_prompt,
            temperature=context.temperature,
            max_tokens=context.max_tokens
        )

        # Extract final answer from CoT response
        return self._extract_cot_answer(response)

    async def _process_react(self, context: BrainContext) -> str:
        """ReAct reasoning with tool use"""
        max_iterations = self.config.max_iterations
        iteration = 0

        while iteration < max_iterations:
            # Generate thought
            thought = await self._generate_thought(context)
            self._thought_history.append(thought)

            if thought.is_final:
                return thought.thought

            if thought.action and thought.action in self._tools:
                # Execute tool
                observation = await self._execute_tool(
                    thought.action,
                    thought.action_input or {}
                )
                thought.observation = observation

                # Add observation to context
                context.messages.append({
                    "role": MessageRole.ASSISTANT.value,
                    "content": f"Thought: {thought.thought}\nAction: {thought.action}\nAction Input: {thought.action_input}"
                })
                context.messages.append({
                    "role": MessageRole.USER.value,
                    "content": f"Observation: {observation}"
                })

            iteration += 1

        return "Maximum iterations reached. Please try a more specific query."

    async def _generate_thought(self, context: BrainContext) -> ThoughtProcess:
        """Generate a single thought in ReAct loop"""
        react_prompt = self._build_react_prompt(context)

        response = await self._llm_client.generate(
            messages=context.messages + [{"role": "user", "content": react_prompt}],
            system=context.system_prompt,
            temperature=context.temperature,
            max_tokens=1024,
            stop_sequences=["Observation:"]
        )

        return self._parse_react_response(response)

    def _build_cot_prompt(self, context: BrainContext) -> str:
        """Build Chain of Thought prompt"""
        original = context.messages[-1]["content"]
        return f"""Let's solve this step by step:

Question: {original}

Think through this carefully:
1. First, let me understand what's being asked...
2. Then, I'll break down the problem...
3. Finally, I'll arrive at the answer...

Let me work through this:"""

    def _build_react_prompt(self, context: BrainContext) -> str:
        """Build ReAct prompt"""
        tools_desc = "\n".join([
            f"- {name}: {info.get('description', 'No description')}"
            for name, info in self._tools.items()
        ])

        return f"""Available tools:
{tools_desc}

Use this format:
Thought: [your reasoning about what to do]
Action: [tool name to use]
Action Input: [input for the tool as JSON]

Or if you have the final answer:
Thought: [your final reasoning]
Final Answer: [your response to the user]

What is your next step?"""

    def _parse_react_response(self, response: str) -> ThoughtProcess:
        """Parse ReAct response into ThoughtProcess"""
        lines = response.strip().split("\n")
        thought = ""
        action = None
        action_input = None
        is_final = False

        for line in lines:
            line = line.strip()
            if line.startswith("Thought:"):
                thought = line[8:].strip()
            elif line.startswith("Action:"):
                action = line[7:].strip()
            elif line.startswith("Action Input:"):
                import json
                try:
                    action_input = json.loads(line[13:].strip())
                except:
                    action_input = {"input": line[13:].strip()}
            elif line.startswith("Final Answer:"):
                thought = line[13:].strip()
                is_final = True

        return ThoughtProcess(
            thought=thought,
            action=action,
            action_input=action_input,
            is_final=is_final
        )

    def _extract_cot_answer(self, response: str) -> str:
        """Extract final answer from CoT response"""
        # Look for explicit final answer markers
        markers = ["Therefore,", "Thus,", "So,", "The answer is", "In conclusion"]
        for marker in markers:
            if marker in response:
                parts = response.split(marker)
                if len(parts) > 1:
                    return marker + parts[-1].strip()
        return response

    async def _execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Execute a tool and return observation"""
        if tool_name not in self._tools:
            return f"Error: Tool '{tool_name}' not found"

        tool_info = self._tools[tool_name]
        tool_func = tool_info["function"]

        try:
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**tool_input)
            else:
                result = tool_func(**tool_input)
            return str(result)
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return f"Error executing {tool_name}: {str(e)}"

    def register_tool(
        self,
        name: str,
        function: Callable,
        description: str = ""
    ) -> None:
        """Register a tool"""
        self._tools[name] = {
            "function": function,
            "description": description,
            "name": name
        }

    def get_thought_history(self) -> List[ThoughtProcess]:
        """Get reasoning history"""
        return self._thought_history.copy()

    def clear_thoughts(self) -> None:
        """Clear thought history"""
        self._thought_history = []

    def set_system_prompt(self, prompt: str) -> None:
        """Set system prompt - Direct, no filtering"""
        self._system_prompt = prompt

    def get_system_prompt(self) -> str:
        """Get current system prompt"""
        return self._system_prompt
