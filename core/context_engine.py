"""
NEXUS AI Agent - Context Engine
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from config.logging_config import get_logger
from config.constants import MessageRole
from prompts.system_prompts import DEFAULT_SYSTEM_PROMPT, get_system_prompt, SYSTEM_PROMPTS


logger = get_logger(__name__)


@dataclass
class Message:
    """Represents a conversation message"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0


@dataclass
class ContextWindow:
    """Represents the current context window"""
    messages: List[Message]
    system_prompt: str
    total_tokens: int
    max_tokens: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_messages_as_dicts(self) -> List[Dict[str, str]]:
        """Convert messages to list of dicts for LLM API"""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]


class ContextEngine:
    """
    Manages conversation context and context window

    Handles:
    - Message history management
    - Context window optimization
    - Token counting and limits
    - Context compression
    """

    def __init__(
        self,
        max_tokens: int = 49000,
        system_prompt: str = None
    ):
        self._messages: List[Message] = []
        # Use DEFAULT_SYSTEM_PROMPT if none provided - Direct connection, no filtering
        self._system_prompt = system_prompt if system_prompt is not None else DEFAULT_SYSTEM_PROMPT
        self._max_tokens = max_tokens
        self._current_tokens = 0
        self._metadata: Dict[str, Any] = {}

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to the context"""
        token_count = self._estimate_tokens(content)

        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
            token_count=token_count
        )

        self._messages.append(message)
        self._current_tokens += token_count

        # Trim if over limit
        self._trim_context()

        logger.debug(f"Added message: {role.value} ({token_count} tokens)")

    def add_user_message(self, content: str) -> None:
        """Add a user message"""
        self.add_message(MessageRole.USER, content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message"""
        self.add_message(MessageRole.ASSISTANT, content)

    def add_system_message(self, content: str) -> None:
        """Add a system message"""
        self.add_message(MessageRole.SYSTEM, content)

    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt directly - No filtering"""
        self._system_prompt = prompt

    def set_system_prompt_by_type(self, prompt_type: str) -> bool:
        """Set system prompt by type (default, coder, researcher, analyst, assistant, etc.)"""
        prompt = get_system_prompt(prompt_type)
        if prompt:
            self._system_prompt = prompt
            return True
        return False

    def get_system_prompt(self) -> str:
        """Get current system prompt"""
        return self._system_prompt

    async def build_context(
        self,
        prompt: str,
        additional_context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> "ContextWindow":
        """
        Build context for LLM call

        Args:
            prompt: Current user prompt
            additional_context: Additional context to include
            history: Conversation history

        Returns:
            ContextWindow object
        """
        # Add history if provided
        if history:
            for msg in history:
                role = MessageRole(msg.get("role", "user"))
                self.add_message(role, msg.get("content", ""))

        # Add current prompt
        self.add_user_message(prompt)

        # Build context window
        messages = self._get_messages_for_context()

        # Inject additional context if provided
        if additional_context:
            context_str = self._format_additional_context(additional_context)
            if context_str:
                messages.insert(0, Message(
                    role=MessageRole.SYSTEM,
                    content=context_str,
                    token_count=self._estimate_tokens(context_str)
                ))

        return ContextWindow(
            messages=messages,
            system_prompt=self._system_prompt,
            total_tokens=self._current_tokens,
            max_tokens=self._max_tokens,
            metadata=self._metadata
        )

    def _get_messages_for_context(self) -> List[Message]:
        """Get messages that fit in context window"""
        available_tokens = self._max_tokens - self._estimate_tokens(self._system_prompt)
        messages = []
        current_tokens = 0

        # Process messages from newest to oldest
        for message in reversed(self._messages):
            if current_tokens + message.token_count <= available_tokens:
                messages.insert(0, message)
                current_tokens += message.token_count
            else:
                break

        return messages

    def _trim_context(self) -> None:
        """Trim context to fit within token limit"""
        while self._current_tokens > self._max_tokens and len(self._messages) > 1:
            removed = self._messages.pop(0)
            self._current_tokens -= removed.token_count
            logger.debug(f"Trimmed message ({removed.token_count} tokens)")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4 + 1

    def _format_additional_context(self, context: Dict[str, Any]) -> str:
        """Format additional context as string"""
        parts = []
        for key, value in context.items():
            if isinstance(value, list):
                value_str = "\n".join(str(v) for v in value)
            elif isinstance(value, dict):
                value_str = "\n".join(f"  {k}: {v}" for k, v in value.items())
            else:
                value_str = str(value)
            parts.append(f"{key}:\n{value_str}")

        return "\n\n".join(parts)

    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages as dictionaries"""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self._messages
        ]

    def get_last_message(self) -> Optional[Message]:
        """Get the last message"""
        return self._messages[-1] if self._messages else None

    def get_message_count(self) -> int:
        """Get total message count"""
        return len(self._messages)

    def get_token_count(self) -> int:
        """Get current token count"""
        return self._current_tokens

    def summarize_context(self, llm_call=None) -> str:
        """Generate a summary of current context"""
        if not self._messages:
            return "No context available."

        summary_parts = []
        for msg in self._messages[-5:]:  # Last 5 messages
            role = msg.role.value.capitalize()
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"{role}: {content}")

        return "\n".join(summary_parts)

    def clear(self) -> None:
        """Clear all context"""
        self._messages = []
        self._current_tokens = 0
        self._metadata = {}

    def set_metadata(self, key: str, value: Any) -> None:
        """Set context metadata"""
        self._metadata[key] = value

    def get_metadata(self, key: str) -> Any:
        """Get context metadata"""
        return self._metadata.get(key)
