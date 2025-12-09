"""
NEXUS AI Agent - Token Optimizer
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class TokenStats:
    """Token statistics"""
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    context_utilization: float = 0.0


class TokenOptimizer:
    """
    Optimizes token usage

    Features:
    - Token counting
    - Context window optimization
    - Message truncation
    - Token budgeting
    """

    def __init__(self, default_model: str = "gpt-4o"):
        self._default_model = default_model
        self._encoding = None
        self._load_encoding()

    def _load_encoding(self) -> None:
        """Load tiktoken encoding"""
        try:
            import tiktoken
            try:
                self._encoding = tiktoken.encoding_for_model(self._default_model)
            except KeyError:
                self._encoding = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            logger.warning("tiktoken not installed, using estimation")
            self._encoding = None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Text to count

        Returns:
            Token count
        """
        if self._encoding:
            return len(self._encoding.encode(text))
        # Fallback estimation
        return len(text) // 4

    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count tokens in messages

        Args:
            messages: List of chat messages

        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            # Account for message overhead (role, separators)
            total += 4  # Message overhead
            total += self.count_tokens(msg.get("content", ""))
            if msg.get("name"):
                total += self.count_tokens(msg["name"])
        total += 2  # Reply priming
        return total

    def truncate_to_tokens(
        self,
        text: str,
        max_tokens: int,
        suffix: str = "..."
    ) -> str:
        """
        Truncate text to fit within token limit

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens
            suffix: Suffix for truncated text

        Returns:
            Truncated text
        """
        if self._encoding:
            tokens = self._encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text

            suffix_tokens = self._encoding.encode(suffix)
            max_content_tokens = max_tokens - len(suffix_tokens)

            truncated_tokens = tokens[:max_content_tokens]
            return self._encoding.decode(truncated_tokens) + suffix

        # Fallback: estimate 4 chars per token
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars - len(suffix)] + suffix

    def optimize_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        preserve_system: bool = True,
        preserve_last_n: int = 2
    ) -> List[Dict[str, str]]:
        """
        Optimize messages to fit within token budget

        Args:
            messages: List of messages
            max_tokens: Maximum total tokens
            preserve_system: Keep system message
            preserve_last_n: Number of recent messages to preserve

        Returns:
            Optimized message list
        """
        if not messages:
            return []

        current_tokens = self.count_message_tokens(messages)
        if current_tokens <= max_tokens:
            return messages

        optimized = []
        reserved_tokens = 0

        # Preserve system message
        system_msgs = []
        if preserve_system:
            system_msgs = [m for m in messages if m.get("role") == "system"]
            for msg in system_msgs:
                reserved_tokens += self.count_tokens(msg.get("content", "")) + 4

        # Preserve last N messages
        last_msgs = messages[-preserve_last_n:] if preserve_last_n else []
        for msg in last_msgs:
            reserved_tokens += self.count_tokens(msg.get("content", "")) + 4

        available_tokens = max_tokens - reserved_tokens

        # Get middle messages
        start_idx = len(system_msgs)
        end_idx = len(messages) - preserve_last_n
        middle_msgs = messages[start_idx:end_idx] if end_idx > start_idx else []

        # Add system messages
        optimized.extend(system_msgs)

        # Add middle messages that fit
        for msg in middle_msgs:
            msg_tokens = self.count_tokens(msg.get("content", "")) + 4
            if available_tokens >= msg_tokens:
                optimized.append(msg)
                available_tokens -= msg_tokens
            else:
                break

        # Add preserved last messages
        optimized.extend(last_msgs)

        return optimized

    def summarize_for_context(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        summarizer: Optional[callable] = None
    ) -> List[Dict[str, str]]:
        """
        Summarize older messages to fit context

        Args:
            messages: Messages to process
            max_tokens: Token budget
            summarizer: Function to summarize text

        Returns:
            Messages with summarized history
        """
        current_tokens = self.count_message_tokens(messages)
        if current_tokens <= max_tokens:
            return messages

        # Split into old and recent
        split_point = len(messages) // 2
        old_messages = messages[:split_point]
        recent_messages = messages[split_point:]

        # Create summary of old messages
        old_content = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in old_messages
        ])

        if summarizer:
            summary = summarizer(old_content)
        else:
            # Simple truncation if no summarizer
            max_summary_tokens = max_tokens // 4
            summary = self.truncate_to_tokens(old_content, max_summary_tokens)

        # Create summary message
        summary_msg = {
            "role": "system",
            "content": f"Previous conversation summary:\n{summary}"
        }

        return [summary_msg] + recent_messages

    def estimate_response_tokens(
        self,
        messages: List[Dict[str, str]],
        model: str,
        context_window: int = 128000
    ) -> int:
        """
        Estimate available tokens for response

        Args:
            messages: Input messages
            model: Model name
            context_window: Model's context window

        Returns:
            Estimated available tokens
        """
        input_tokens = self.count_message_tokens(messages)
        available = context_window - input_tokens

        # Leave some buffer
        return max(0, available - 100)

    def split_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int = 0
    ) -> List[str]:
        """
        Split text into token-sized chunks

        Args:
            text: Text to split
            chunk_size: Tokens per chunk
            overlap: Overlap tokens between chunks

        Returns:
            List of text chunks
        """
        if self._encoding:
            tokens = self._encoding.encode(text)
            chunks = []
            start = 0

            while start < len(tokens):
                end = min(start + chunk_size, len(tokens))
                chunk_tokens = tokens[start:end]
                chunks.append(self._encoding.decode(chunk_tokens))
                start = end - overlap if overlap else end

            return chunks

        # Fallback: character-based splitting
        char_size = chunk_size * 4
        char_overlap = overlap * 4
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + char_size, len(text))
            chunks.append(text[start:end])
            start = end - char_overlap if char_overlap else end

        return chunks

    def get_stats(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        context_window: int = 128000
    ) -> TokenStats:
        """
        Get token statistics

        Args:
            messages: Messages to analyze
            model: Model name
            context_window: Model context window

        Returns:
            TokenStats object
        """
        input_tokens = self.count_message_tokens(messages)

        return TokenStats(
            total_tokens=input_tokens,
            input_tokens=input_tokens,
            output_tokens=0,  # Not yet generated
            estimated_cost=self._estimate_cost(input_tokens, 0, model),
            context_utilization=input_tokens / context_window
        )

    def _estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Estimate cost based on model pricing"""
        pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
        }

        for model_prefix, prices in pricing.items():
            if model_prefix in model:
                return (
                    (input_tokens / 1000) * prices["input"] +
                    (output_tokens / 1000) * prices["output"]
                )

        return 0.0


# Global optimizer instance
token_optimizer = TokenOptimizer()
