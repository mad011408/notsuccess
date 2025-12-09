"""
NEXUS AI Agent - Chain of Thought Reasoning
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ThoughtStep:
    """A single step in chain of thought"""
    step_number: int
    thought: str
    reasoning: str = ""
    conclusion: str = ""
    confidence: float = 0.0


@dataclass
class ChainOfThoughtResult:
    """Result of CoT reasoning"""
    query: str
    steps: List[ThoughtStep]
    final_answer: str
    confidence: float
    reasoning_trace: str


class ChainOfThought:
    """
    Chain of Thought Reasoning Strategy

    Breaks down complex problems into sequential reasoning steps.
    """

    def __init__(self, num_steps: int = 5, verbose: bool = False):
        self.num_steps = num_steps
        self.verbose = verbose

    async def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        llm_call: Optional[Callable] = None
    ) -> ChainOfThoughtResult:
        """
        Perform chain of thought reasoning

        Args:
            query: Question to answer
            context: Additional context
            llm_call: Function to call LLM

        Returns:
            ChainOfThoughtResult with reasoning steps
        """
        if not llm_call:
            raise ValueError("llm_call function required")

        prompt = self._build_prompt(query, context)
        response = await llm_call(prompt)

        steps = self._parse_steps(response)
        final_answer = self._extract_answer(response, steps)
        confidence = self._calculate_confidence(steps)

        return ChainOfThoughtResult(
            query=query,
            steps=steps,
            final_answer=final_answer,
            confidence=confidence,
            reasoning_trace=response
        )

    def _build_prompt(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build CoT prompt"""
        context_str = ""
        if context:
            context_str = f"\nContext: {context}\n"

        return f"""Let's think through this step by step.
{context_str}
Question: {query}

Break down your reasoning into clear steps:

Step 1: First, let me understand what is being asked...

Step 2: Now, let me consider the key factors...

Step 3: Based on my analysis...

Continue until you reach a conclusion.

Final Answer: [Your answer]"""

    def _parse_steps(self, response: str) -> List[ThoughtStep]:
        """Parse reasoning steps from response"""
        steps = []
        lines = response.split("\n")
        current_step = None
        current_content = []

        for line in lines:
            line = line.strip()
            if line.lower().startswith("step"):
                if current_step is not None:
                    steps.append(ThoughtStep(
                        step_number=current_step,
                        thought="\n".join(current_content),
                        confidence=0.8
                    ))
                # Extract step number
                try:
                    parts = line.split(":")
                    step_part = parts[0].lower().replace("step", "").strip()
                    current_step = int(step_part)
                    current_content = [":".join(parts[1:]).strip()] if len(parts) > 1 else []
                except:
                    current_content.append(line)
            elif current_step is not None:
                if not line.lower().startswith("final"):
                    current_content.append(line)

        # Add last step
        if current_step is not None and current_content:
            steps.append(ThoughtStep(
                step_number=current_step,
                thought="\n".join(current_content),
                confidence=0.8
            ))

        return steps

    def _extract_answer(
        self,
        response: str,
        steps: List[ThoughtStep]
    ) -> str:
        """Extract final answer from response"""
        # Look for explicit final answer
        lower_response = response.lower()
        markers = ["final answer:", "therefore:", "thus:", "in conclusion:", "the answer is:"]

        for marker in markers:
            if marker in lower_response:
                idx = lower_response.index(marker)
                answer = response[idx + len(marker):].strip()
                # Take until next newline or end
                if "\n" in answer:
                    answer = answer.split("\n")[0]
                return answer

        # Use last step conclusion if no explicit answer
        if steps:
            return steps[-1].thought

        return response.strip()

    def _calculate_confidence(self, steps: List[ThoughtStep]) -> float:
        """Calculate overall confidence"""
        if not steps:
            return 0.5

        # More steps with clear reasoning = higher confidence
        base_confidence = min(0.9, 0.5 + len(steps) * 0.1)

        # Average step confidence
        avg_step_conf = sum(s.confidence for s in steps) / len(steps)

        return (base_confidence + avg_step_conf) / 2

    async def reason_with_examples(
        self,
        query: str,
        examples: List[Dict[str, str]],
        llm_call: Callable
    ) -> ChainOfThoughtResult:
        """
        Few-shot CoT with examples

        Args:
            query: Question to answer
            examples: List of {"question": ..., "reasoning": ..., "answer": ...}
            llm_call: LLM function

        Returns:
            ChainOfThoughtResult
        """
        # Build few-shot prompt
        examples_str = ""
        for i, ex in enumerate(examples):
            examples_str += f"""
Example {i + 1}:
Question: {ex['question']}
Reasoning: {ex['reasoning']}
Answer: {ex['answer']}
"""

        prompt = f"""Here are some examples of step-by-step reasoning:
{examples_str}

Now, let's solve this problem step by step:

Question: {query}

Let me think through this carefully..."""

        response = await llm_call(prompt)
        steps = self._parse_steps(response)
        final_answer = self._extract_answer(response, steps)

        return ChainOfThoughtResult(
            query=query,
            steps=steps,
            final_answer=final_answer,
            confidence=self._calculate_confidence(steps),
            reasoning_trace=response
        )

    async def zero_shot_cot(
        self,
        query: str,
        llm_call: Callable
    ) -> ChainOfThoughtResult:
        """
        Zero-shot CoT with "Let's think step by step"

        Args:
            query: Question
            llm_call: LLM function

        Returns:
            ChainOfThoughtResult
        """
        prompt = f"{query}\n\nLet's think step by step."

        response = await llm_call(prompt)
        steps = self._parse_steps(response)
        final_answer = self._extract_answer(response, steps)

        return ChainOfThoughtResult(
            query=query,
            steps=steps,
            final_answer=final_answer,
            confidence=self._calculate_confidence(steps),
            reasoning_trace=response
        )
