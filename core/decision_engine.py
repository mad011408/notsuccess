"""
NEXUS AI Agent - Decision Engine
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from config.logging_config import get_logger


logger = get_logger(__name__)


class DecisionType(str, Enum):
    """Types of decisions"""
    TOOL_SELECTION = "tool_selection"
    RESPONSE_TYPE = "response_type"
    ROUTING = "routing"
    ESCALATION = "escalation"
    RETRY = "retry"


@dataclass
class Decision:
    """Represents a decision made by the engine"""
    decision_type: DecisionType
    choice: str
    confidence: float
    reasoning: str
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionContext:
    """Context for making decisions"""
    query: str
    available_options: List[str]
    constraints: Dict[str, Any] = field(default_factory=dict)
    history: List[Decision] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)


class DecisionStrategy:
    """Base class for decision strategies"""

    async def decide(
        self,
        context: DecisionContext,
        llm_call: Optional[Callable] = None
    ) -> Decision:
        raise NotImplementedError


class RuleBasedDecision(DecisionStrategy):
    """Rule-based decision making"""

    def __init__(self):
        self.rules: List[Dict[str, Any]] = []

    def add_rule(
        self,
        condition: Callable[[DecisionContext], bool],
        choice: str,
        priority: int = 0
    ) -> None:
        """Add a decision rule"""
        self.rules.append({
            "condition": condition,
            "choice": choice,
            "priority": priority
        })
        self.rules.sort(key=lambda x: x["priority"], reverse=True)

    async def decide(
        self,
        context: DecisionContext,
        llm_call: Optional[Callable] = None
    ) -> Decision:
        """Make decision based on rules"""
        for rule in self.rules:
            if rule["condition"](context):
                return Decision(
                    decision_type=DecisionType.ROUTING,
                    choice=rule["choice"],
                    confidence=1.0,
                    reasoning=f"Matched rule with priority {rule['priority']}"
                )

        # Default to first available option
        return Decision(
            decision_type=DecisionType.ROUTING,
            choice=context.available_options[0] if context.available_options else "",
            confidence=0.5,
            reasoning="No rules matched, using default"
        )


class LLMBasedDecision(DecisionStrategy):
    """LLM-based decision making"""

    async def decide(
        self,
        context: DecisionContext,
        llm_call: Optional[Callable] = None
    ) -> Decision:
        """Make decision using LLM"""
        if not llm_call:
            raise ValueError("LLM call function required for LLM-based decisions")

        options_str = "\n".join([
            f"{i + 1}. {opt}" for i, opt in enumerate(context.available_options)
        ])

        prompt = f"""Given this query: {context.query}

Available options:
{options_str}

Choose the best option and explain why.
Format your response as:
Choice: [option number]
Confidence: [0-1]
Reasoning: [explanation]"""

        response = await llm_call(prompt)

        return self._parse_response(response, context)

    def _parse_response(
        self,
        response: str,
        context: DecisionContext
    ) -> Decision:
        """Parse LLM response into Decision"""
        choice_idx = 0
        confidence = 0.5
        reasoning = ""

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("Choice:"):
                try:
                    choice_idx = int(line.split(":")[1].strip()) - 1
                except:
                    pass
            elif line.startswith("Confidence:"):
                try:
                    confidence = float(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("Reasoning:"):
                reasoning = line.split(":", 1)[1].strip()

        choice = context.available_options[choice_idx] if choice_idx < len(context.available_options) else ""

        return Decision(
            decision_type=DecisionType.ROUTING,
            choice=choice,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=[
                {"option": opt, "selected": opt == choice}
                for opt in context.available_options
            ]
        )


class ScoringDecision(DecisionStrategy):
    """Score-based decision making"""

    def __init__(self):
        self.scorers: List[Callable[[str, DecisionContext], float]] = []

    def add_scorer(self, scorer: Callable[[str, DecisionContext], float]) -> None:
        """Add a scoring function"""
        self.scorers.append(scorer)

    async def decide(
        self,
        context: DecisionContext,
        llm_call: Optional[Callable] = None
    ) -> Decision:
        """Make decision based on scores"""
        scores: Dict[str, float] = {}

        for option in context.available_options:
            total_score = 0.0
            for scorer in self.scorers:
                total_score += scorer(option, context)
            scores[option] = total_score / len(self.scorers) if self.scorers else 0.0

        best_option = max(scores, key=scores.get) if scores else ""
        best_score = scores.get(best_option, 0.0)

        return Decision(
            decision_type=DecisionType.ROUTING,
            choice=best_option,
            confidence=best_score,
            reasoning=f"Highest score: {best_score:.2f}",
            alternatives=[
                {"option": opt, "score": score}
                for opt, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
            ]
        )


class DecisionEngine:
    """
    Main Decision Engine

    Handles all decision-making processes for the agent
    """

    def __init__(self):
        self._strategies: Dict[str, DecisionStrategy] = {
            "rule_based": RuleBasedDecision(),
            "llm_based": LLMBasedDecision(),
            "scoring": ScoringDecision()
        }
        self._decision_history: List[Decision] = []
        self._llm_call: Optional[Callable] = None

    def set_llm_call(self, llm_call: Callable) -> None:
        """Set LLM call function"""
        self._llm_call = llm_call

    async def decide(
        self,
        query: str,
        options: List[str],
        strategy: str = "llm_based",
        constraints: Optional[Dict[str, Any]] = None
    ) -> Decision:
        """
        Make a decision

        Args:
            query: The decision query
            options: Available options
            strategy: Decision strategy to use
            constraints: Optional constraints

        Returns:
            Decision object
        """
        context = DecisionContext(
            query=query,
            available_options=options,
            constraints=constraints or {},
            history=self._decision_history
        )

        strategy_impl = self._strategies.get(strategy)
        if not strategy_impl:
            raise ValueError(f"Unknown strategy: {strategy}")

        decision = await strategy_impl.decide(context, self._llm_call)
        self._decision_history.append(decision)

        logger.info(f"Decision made: {decision.choice} (confidence: {decision.confidence})")

        return decision

    async def select_tool(
        self,
        query: str,
        available_tools: List[Dict[str, Any]]
    ) -> Decision:
        """Select the best tool for a query"""
        tool_names = [t["name"] for t in available_tools]

        context = DecisionContext(
            query=query,
            available_options=tool_names,
            metadata={"tools": available_tools}
        )

        # Use LLM for tool selection with tool descriptions
        tools_desc = "\n".join([
            f"- {t['name']}: {t.get('description', 'No description')}"
            for t in available_tools
        ])

        prompt = f"""Query: {query}

Available tools:
{tools_desc}

Which tool should be used? Respond with just the tool name."""

        if self._llm_call:
            response = await self._llm_call(prompt)
            selected = response.strip()

            # Find matching tool
            for tool in tool_names:
                if tool.lower() in selected.lower():
                    return Decision(
                        decision_type=DecisionType.TOOL_SELECTION,
                        choice=tool,
                        confidence=0.8,
                        reasoning=f"LLM selected {tool} for query"
                    )

        # Fallback to first tool
        return Decision(
            decision_type=DecisionType.TOOL_SELECTION,
            choice=tool_names[0] if tool_names else "",
            confidence=0.5,
            reasoning="Default selection"
        )

    async def should_retry(
        self,
        error: Exception,
        attempt: int,
        max_attempts: int = 3
    ) -> Decision:
        """Decide if operation should be retried"""
        should_retry = attempt < max_attempts

        # Check error type for retry eligibility
        retryable_errors = ["timeout", "rate_limit", "connection", "temporary"]
        error_str = str(error).lower()
        is_retryable = any(e in error_str for e in retryable_errors)

        return Decision(
            decision_type=DecisionType.RETRY,
            choice="retry" if (should_retry and is_retryable) else "fail",
            confidence=0.9 if is_retryable else 0.1,
            reasoning=f"Attempt {attempt}/{max_attempts}, error type: {type(error).__name__}",
            metadata={
                "attempt": attempt,
                "max_attempts": max_attempts,
                "error": str(error),
                "is_retryable": is_retryable
            }
        )

    def get_history(self) -> List[Decision]:
        """Get decision history"""
        return self._decision_history.copy()

    def clear_history(self) -> None:
        """Clear decision history"""
        self._decision_history = []
