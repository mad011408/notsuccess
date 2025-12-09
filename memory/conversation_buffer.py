"""
NEXUS AI Agent - Conversation Buffer Memory
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class Message:
    """A conversation message"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationBuffer:
    """
    Simple conversation buffer memory

    Stores full conversation history up to a limit.
    """

    def __init__(self, max_messages: int = 100):
        self._messages: List[Message] = []
        self._max_messages = max_messages

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to the buffer"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self._messages.append(message)

        # Trim if over limit
        while len(self._messages) > self._max_messages:
            self._messages.pop(0)

    def add_user_message(self, content: str) -> None:
        """Add a user message"""
        self.add_message("user", content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message"""
        self.add_message("assistant", content)

    def add_system_message(self, content: str) -> None:
        """Add a system message"""
        self.add_message("system", content)

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get messages as list of dicts

        Args:
            limit: Maximum messages to return

        Returns:
            List of message dicts
        """
        messages = self._messages
        if limit:
            messages = messages[-limit:]

        return [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

    def get_history_string(self, limit: Optional[int] = None) -> str:
        """Get history as formatted string"""
        messages = self._messages
        if limit:
            messages = messages[-limit:]

        return "\n".join([
            f"{m.role.capitalize()}: {m.content}"
            for m in messages
        ])

    def get_last_message(self) -> Optional[Message]:
        """Get the last message"""
        return self._messages[-1] if self._messages else None

    def get_last_user_message(self) -> Optional[Message]:
        """Get the last user message"""
        for msg in reversed(self._messages):
            if msg.role == "user":
                return msg
        return None

    def get_last_assistant_message(self) -> Optional[Message]:
        """Get the last assistant message"""
        for msg in reversed(self._messages):
            if msg.role == "assistant":
                return msg
        return None

    def clear(self) -> None:
        """Clear all messages"""
        self._messages = []

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self):
        return iter(self._messages)
