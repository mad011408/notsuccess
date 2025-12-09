"""
NEXUS AI Agent - Memory Compressor
"""

from typing import Optional, List, Dict, Any, Callable

from config.logging_config import get_logger


logger = get_logger(__name__)


class MemoryCompressor:
    """
    Compresses memories to save space

    Methods:
    - Summarization
    - Deduplication
    - Importance filtering
    """

    def __init__(self, llm_call: Optional[Callable] = None):
        self._llm_call = llm_call

    def set_llm_call(self, llm_call: Callable) -> None:
        """Set LLM call function"""
        self._llm_call = llm_call

    async def compress(
        self,
        memories: List[Dict[str, Any]],
        target_count: Optional[int] = None,
        target_tokens: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Compress memories

        Args:
            memories: Memories to compress
            target_count: Target number of memories
            target_tokens: Target token count

        Returns:
            Compressed memories
        """
        if not memories:
            return []

        # Deduplicate
        deduped = self._deduplicate(memories)

        # Summarize if LLM available and too many
        if self._llm_call and target_count and len(deduped) > target_count:
            deduped = await self._summarize_memories(deduped, target_count)

        # Filter by importance if still too many
        if target_count and len(deduped) > target_count:
            deduped = self._filter_by_importance(deduped, target_count)

        return deduped

    def _deduplicate(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate memories"""
        seen = set()
        unique = []

        for memory in memories:
            content = memory.get("content", "")
            # Simple dedup by content hash
            content_hash = hash(content.strip().lower())

            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(memory)

        return unique

    async def _summarize_memories(
        self,
        memories: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Summarize memories using LLM"""
        if len(memories) <= target_count:
            return memories

        # Group memories and summarize
        group_size = len(memories) // target_count + 1
        summarized = []

        for i in range(0, len(memories), group_size):
            group = memories[i:i + group_size]

            if len(group) == 1:
                summarized.append(group[0])
            else:
                # Summarize group
                contents = "\n".join([m.get("content", "") for m in group])
                prompt = f"Summarize these memories concisely:\n{contents}\n\nSummary:"

                summary = await self._llm_call(prompt)
                summarized.append({
                    "content": summary,
                    "importance": max(m.get("importance", 0.5) for m in group),
                    "compressed": True
                })

        return summarized

    def _filter_by_importance(
        self,
        memories: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Keep only most important memories"""
        sorted_memories = sorted(
            memories,
            key=lambda m: m.get("importance", 0.5),
            reverse=True
        )
        return sorted_memories[:target_count]

    def estimate_tokens(self, memories: List[Dict[str, Any]]) -> int:
        """Estimate total tokens"""
        total_chars = sum(
            len(m.get("content", ""))
            for m in memories
        )
        return total_chars // 4
