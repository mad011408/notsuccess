"""
NEXUS AI Agent - Self-Consistency Reasoning
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from collections import Counter

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class SelfConsistencyResult:
    """Result of self-consistency reasoning"""
    query: str
    responses: List[str]
    final_answer: str
    confidence: float
    agreement_ratio: float


class SelfConsistency:
    """
    Self-Consistency Reasoning Strategy

    Generates multiple reasoning paths and selects the most consistent answer.
    """

    def __init__(self, num_samples: int = 5, temperature: float = 0.7):
        self.num_samples = num_samples
        self.temperature = temperature

    async def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        llm_call: Optional[Callable] = None
    ) -> SelfConsistencyResult:
        """
        Perform self-consistency reasoning

        Args:
            query: Question to answer
            context: Additional context
            llm_call: Function to call LLM

        Returns:
            SelfConsistencyResult
        """
        if not llm_call:
            raise ValueError("llm_call function required")

        # Generate multiple responses
        responses = []
        for i in range(self.num_samples):
            prompt = self._build_prompt(query, context)
            response = await llm_call(prompt)
            responses.append(response)

        # Extract answers from responses
        answers = [self._extract_answer(r) for r in responses]

        # Find most common answer
        answer_counts = Counter(answers)
        most_common = answer_counts.most_common(1)[0]
        final_answer = most_common[0]
        agreement_count = most_common[1]

        return SelfConsistencyResult(
            query=query,
            responses=responses,
            final_answer=final_answer,
            confidence=agreement_count / self.num_samples,
            agreement_ratio=agreement_count / self.num_samples
        )

    def _build_prompt(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for self-consistency"""
        context_str = f"\nContext: {context}\n" if context else ""

        return f"""Let's solve this step by step.
{context_str}
Question: {query}

Think through this carefully and provide your answer.
At the end, clearly state: "The answer is: [your answer]"
"""

    def _extract_answer(self, response: str) -> str:
        """Extract answer from response"""
        lower = response.lower()

        # Look for explicit answer markers
        markers = ["the answer is:", "answer:", "therefore,", "thus,", "so,"]

        for marker in markers:
            if marker in lower:
                idx = lower.index(marker) + len(marker)
                answer = response[idx:].strip()
                # Take first line or sentence
                answer = answer.split("\n")[0].split(".")[0].strip()
                return answer

        # Return last sentence as fallback
        sentences = response.strip().split(".")
        return sentences[-1].strip() if sentences else response.strip()

    async def reason_with_voting(
        self,
        query: str,
        llm_call: Callable,
        normalize_fn: Optional[Callable] = None
    ) -> SelfConsistencyResult:
        """
        Self-consistency with answer normalization

        Args:
            query: Question
            llm_call: LLM function
            normalize_fn: Function to normalize answers for comparison

        Returns:
            SelfConsistencyResult
        """
        responses = []
        for _ in range(self.num_samples):
            response = await llm_call(self._build_prompt(query))
            responses.append(response)

        # Extract and normalize answers
        answers = [self._extract_answer(r) for r in responses]
        if normalize_fn:
            normalized = [normalize_fn(a) for a in answers]
        else:
            normalized = [a.lower().strip() for a in answers]

        # Vote
        answer_counts = Counter(normalized)
        most_common_normalized = answer_counts.most_common(1)[0][0]

        # Find original answer format
        for ans, norm in zip(answers, normalized):
            if norm == most_common_normalized:
                final_answer = ans
                break
        else:
            final_answer = most_common_normalized

        agreement = answer_counts[most_common_normalized] / self.num_samples

        return SelfConsistencyResult(
            query=query,
            responses=responses,
            final_answer=final_answer,
            confidence=agreement,
            agreement_ratio=agreement
        )
