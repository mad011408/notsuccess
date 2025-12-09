"""
NEXUS AI Agent - Sliding Window Memory
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class WindowMessage:
    """Message in sliding window"""
    role: str
    content: str
    tokens: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SlidingWindowMemory:
    """
    Sliding window memory with token limit

    Keeps most recent messages within token budget.
    """

    def __init__(self, max_tokens: int = 4000):
        self._messages: List[WindowMessage] = []
        self._max_tokens = max_tokens
        self._current_tokens = 0

    def add_message(
        self,
        role: str,
        content: str,
        tokens: Optional[int] = None
    ) -> None:
        """Add a message to the window"""
        if tokens is None:
            tokens = len(content) // 4  # Estimate

        message = WindowMessage(
            role=role,
            content=content,
            tokens=tokens
        )

        self._messages.append(message)
        self._current_tokens += tokens

        # Slide window
        self._slide()

    def _slide(self) -> None:
        """Slide window to fit within token limit"""
        while self._current_tokens > self._max_tokens and len(self._messages) > 1:
            removed = self._messages.pop(0)
            self._current_tokens -= removed.tokens

    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages in window"""
        return [
            {"role": m.role, "content": m.content}
            for m in self._messages
        ]

    def get_token_count(self) -> int:
        """Get current token count"""
        return self._current_tokens

    def get_available_tokens(self) -> int:
        """Get available tokens"""
        return self._max_tokens - self._current_tokens

    def resize(self, new_max_tokens: int) -> None:
        """Resize window"""
        self._max_tokens = new_max_tokens
        self._slide()

    def clear(self) -> None:
        """Clear window"""
        self._messages = []
        self._current_tokens = 0

    def __len__(self) -> int:
        return len(self._messages)
