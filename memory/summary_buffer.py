"""
NEXUS AI Agent - Summary Buffer Memory
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class SummaryState:
    """Current summary state"""
    summary: str = ""
    recent_messages: List[Dict[str, str]] = None
    message_count: int = 0

    def __post_init__(self):
        if self.recent_messages is None:
            self.recent_messages = []


class SummaryBuffer:
    """
    Summary buffer memory

    Summarizes older messages while keeping recent ones.
    """

    def __init__(
        self,
        max_recent: int = 10,
        summarize_threshold: int = 15,
        llm_call: Optional[Callable] = None
    ):
        self._state = SummaryState()
        self._max_recent = max_recent
        self._summarize_threshold = summarize_threshold
        self._llm_call = llm_call

    def set_llm_call(self, llm_call: Callable) -> None:
        """Set LLM call function for summarization"""
        self._llm_call = llm_call

    def add_message(self, role: str, content: str) -> None:
        """Add a message"""
        self._state.recent_messages.append({
            "role": role,
            "content": content
        })
        self._state.message_count += 1

    async def process(self) -> None:
        """Process and summarize if needed"""
        if len(self._state.recent_messages) >= self._summarize_threshold:
            await self._summarize()

    async def _summarize(self) -> None:
        """Summarize older messages"""
        if not self._llm_call:
            # Simple fallback without LLM
            to_summarize = self._state.recent_messages[:-self._max_recent]
            summary_text = "\n".join([
                f"{m['role']}: {m['content'][:100]}..."
                for m in to_summarize
            ])
            self._state.summary = f"Previous conversation summary:\n{summary_text}"
        else:
            # Use LLM for summarization
            to_summarize = self._state.recent_messages[:-self._max_recent]
            conversation = "\n".join([
                f"{m['role']}: {m['content']}"
                for m in to_summarize
            ])

            prompt = f"""Summarize this conversation concisely:

{conversation}

Summary:"""

            new_summary = await self._llm_call(prompt)

            if self._state.summary:
                self._state.summary = f"{self._state.summary}\n\n{new_summary}"
            else:
                self._state.summary = new_summary

        # Keep only recent messages
        self._state.recent_messages = self._state.recent_messages[-self._max_recent:]

    def get_context(self) -> List[Dict[str, str]]:
        """Get context for LLM"""
        messages = []

        if self._state.summary:
            messages.append({
                "role": "system",
                "content": f"Conversation summary: {self._state.summary}"
            })

        messages.extend(self._state.recent_messages)

        return messages

    def get_summary(self) -> str:
        """Get current summary"""
        return self._state.summary

    def clear(self) -> None:
        """Clear all memory"""
        self._state = SummaryState()
