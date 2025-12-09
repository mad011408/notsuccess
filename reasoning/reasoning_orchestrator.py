"""
NEXUS AI Agent - Reasoning Orchestrator
"""

from typing import Optional, Dict, Any, Callable
from enum import Enum

from .chain_of_thought import ChainOfThought
from .tree_of_thought import TreeOfThought
from .react_strategy import ReActStrategy
from .reflexion_strategy import ReflexionStrategy
from .self_consistency import SelfConsistency

from config.logging_config import get_logger


logger = get_logger(__name__)


class ReasoningType(str, Enum):
    """Types of reasoning strategies"""
    CHAIN_OF_THOUGHT = "cot"
    TREE_OF_THOUGHT = "tot"
    REACT = "react"
    REFLEXION = "reflexion"
    SELF_CONSISTENCY = "self_consistency"
    AUTO = "auto"


class ReasoningOrchestrator:
    """
    Orchestrates different reasoning strategies

    Selects and executes appropriate reasoning based on task type.
    """

    def __init__(self):
        self._strategies = {
            ReasoningType.CHAIN_OF_THOUGHT: ChainOfThought(),
            ReasoningType.TREE_OF_THOUGHT: TreeOfThought(),
            ReasoningType.REACT: ReActStrategy(),
            ReasoningType.REFLEXION: ReflexionStrategy(),
            ReasoningType.SELF_CONSISTENCY: SelfConsistency(),
        }
        self._llm_call: Optional[Callable] = None

    def set_llm_call(self, llm_call: Callable) -> None:
        """Set the LLM call function"""
        self._llm_call = llm_call

    async def reason(
        self,
        query: str,
        strategy: ReasoningType = ReasoningType.AUTO,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute reasoning with specified strategy

        Args:
            query: Question to answer
            strategy: Reasoning strategy to use
            context: Additional context
            **kwargs: Strategy-specific options

        Returns:
            Reasoning result
        """
        if not self._llm_call:
            raise ValueError("LLM call function not set")

        # Auto-select strategy
        if strategy == ReasoningType.AUTO:
            strategy = self._select_strategy(query, context)

        strategy_impl = self._strategies.get(strategy)
        if not strategy_impl:
            raise ValueError(f"Unknown strategy: {strategy}")

        logger.info(f"Using reasoning strategy: {strategy.value}")

        return await strategy_impl.reason(
            query=query,
            context=context,
            llm_call=self._llm_call,
            **kwargs
        )

    def _select_strategy(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningType:
        """Auto-select appropriate strategy"""
        query_lower = query.lower()

        # Action-oriented queries -> ReAct
        action_keywords = ["find", "search", "look up", "calculate", "get"]
        if any(kw in query_lower for kw in action_keywords):
            return ReasoningType.REACT

        # Complex multi-step problems -> Tree of Thought
        complex_keywords = ["compare", "analyze", "evaluate", "design"]
        if any(kw in query_lower for kw in complex_keywords):
            return ReasoningType.TREE_OF_THOUGHT

        # Math/logic problems -> Self-Consistency
        math_keywords = ["solve", "compute", "prove", "math"]
        if any(kw in query_lower for kw in math_keywords):
            return ReasoningType.SELF_CONSISTENCY

        # Default to Chain of Thought
        return ReasoningType.CHAIN_OF_THOUGHT

    def register_strategy(
        self,
        name: str,
        strategy: Any
    ) -> None:
        """Register a custom strategy"""
        self._strategies[name] = strategy

    def get_available_strategies(self) -> list:
        """Get list of available strategies"""
        return list(self._strategies.keys())


# Global orchestrator
reasoning_orchestrator = ReasoningOrchestrator()
