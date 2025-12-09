"""
NEXUS AI Agent - Reflexion Strategy (Self-Reflection)
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ReflexionStep:
    """A step in reflexion loop"""
    attempt: int
    action: str
    result: str
    reflection: str
    improvement: str


@dataclass
class ReflexionResult:
    """Result of reflexion reasoning"""
    query: str
    steps: List[ReflexionStep]
    final_answer: str
    success: bool
    attempts: int


class ReflexionStrategy:
    """
    Reflexion Strategy - Self-Reflection Learning

    Uses self-reflection to improve responses iteratively.
    """

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    async def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        llm_call: Optional[Callable] = None,
        evaluator: Optional[Callable] = None
    ) -> ReflexionResult:
        """
        Perform reflexion reasoning

        Args:
            query: Question to answer
            context: Additional context
            llm_call: Function to call LLM
            evaluator: Function to evaluate response

        Returns:
            ReflexionResult
        """
        if not llm_call:
            raise ValueError("llm_call function required")

        steps: List[ReflexionStep] = []
        memory = []  # Store past reflections

        for attempt in range(1, self.max_attempts + 1):
            # Generate response with memory of past reflections
            response = await self._generate_response(
                query, memory, context, llm_call
            )

            # Evaluate response
            if evaluator:
                is_correct, feedback = await evaluator(query, response)
            else:
                is_correct, feedback = await self._self_evaluate(
                    query, response, llm_call
                )

            if is_correct:
                return ReflexionResult(
                    query=query,
                    steps=steps,
                    final_answer=response,
                    success=True,
                    attempts=attempt
                )

            # Generate reflection
            reflection = await self._reflect(
                query, response, feedback, llm_call
            )

            # Generate improvement plan
            improvement = await self._plan_improvement(
                query, response, reflection, llm_call
            )

            step = ReflexionStep(
                attempt=attempt,
                action=response,
                result=feedback,
                reflection=reflection,
                improvement=improvement
            )
            steps.append(step)
            memory.append(step)

        # Return best attempt
        final_response = await self._generate_response(
            query, memory, context, llm_call
        )

        return ReflexionResult(
            query=query,
            steps=steps,
            final_answer=final_response,
            success=False,
            attempts=self.max_attempts
        )

    async def _generate_response(
        self,
        query: str,
        memory: List[ReflexionStep],
        context: Optional[Dict[str, Any]],
        llm_call: Callable
    ) -> str:
        """Generate response with memory of reflections"""
        memory_str = ""
        if memory:
            memory_str = "\n\nPrevious attempts and reflections:\n"
            for step in memory:
                memory_str += f"\nAttempt {step.attempt}:"
                memory_str += f"\n- Response: {step.action[:200]}..."
                memory_str += f"\n- Feedback: {step.result}"
                memory_str += f"\n- Reflection: {step.reflection}"
                memory_str += f"\n- Improvement: {step.improvement}\n"

        context_str = f"\nContext: {context}\n" if context else ""

        prompt = f"""Question: {query}
{context_str}{memory_str}
Based on any previous reflections, provide your best answer:"""

        return await llm_call(prompt)

    async def _self_evaluate(
        self,
        query: str,
        response: str,
        llm_call: Callable
    ) -> tuple:
        """Self-evaluate the response"""
        prompt = f"""Evaluate this response:

Question: {query}
Response: {response}

Is this response correct and complete?
Respond with:
CORRECT: [yes/no]
FEEDBACK: [explanation]"""

        eval_response = await llm_call(prompt)

        is_correct = "yes" in eval_response.lower().split("correct")[0] if "correct" in eval_response.lower() else False
        feedback = eval_response.split("FEEDBACK:")[-1].strip() if "FEEDBACK:" in eval_response else eval_response

        return is_correct, feedback

    async def _reflect(
        self,
        query: str,
        response: str,
        feedback: str,
        llm_call: Callable
    ) -> str:
        """Generate reflection on the response"""
        prompt = f"""Reflect on this attempt:

Question: {query}
Your Response: {response}
Feedback: {feedback}

What went wrong? What could be improved? Be specific:"""

        return await llm_call(prompt)

    async def _plan_improvement(
        self,
        query: str,
        response: str,
        reflection: str,
        llm_call: Callable
    ) -> str:
        """Plan improvements for next attempt"""
        prompt = f"""Based on this reflection:

Question: {query}
Previous Response: {response}
Reflection: {reflection}

What specific changes should be made in the next attempt?"""

        return await llm_call(prompt)
