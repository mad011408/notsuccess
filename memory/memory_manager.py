"""
NEXUS AI Agent - Memory Manager
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from config.logging_config import get_logger


logger = get_logger(__name__)


class MemoryType(str, Enum):
    """Types of memory"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    WORKING = "working"


@dataclass
class Memory:
    """A memory item"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    memory_type: MemoryType = MemoryType.SHORT_TERM
    importance: float = 0.5
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class MemoryManager:
    """
    Central Memory Manager

    Manages different types of memory:
    - Short-term: Recent conversation context
    - Long-term: Persistent knowledge
    - Episodic: Experience memories
    - Semantic: Factual knowledge
    - Working: Current task context
    """

    def __init__(self, max_short_term: int = 100, max_working: int = 20):
        self._short_term: List[Memory] = []
        self._long_term: Dict[str, Memory] = {}
        self._episodic: Dict[str, Memory] = {}
        self._semantic: Dict[str, Memory] = {}
        self._working: List[Memory] = []

        self._max_short_term = max_short_term
        self._max_working = max_working

    def add(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Add a memory

        Args:
            content: Memory content
            memory_type: Type of memory
            importance: Importance score (0-1)
            metadata: Additional metadata

        Returns:
            Created Memory object
        """
        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {}
        )

        if memory_type == MemoryType.SHORT_TERM:
            self._add_short_term(memory)
        elif memory_type == MemoryType.LONG_TERM:
            self._long_term[memory.id] = memory
        elif memory_type == MemoryType.EPISODIC:
            self._episodic[memory.id] = memory
        elif memory_type == MemoryType.SEMANTIC:
            self._semantic[memory.id] = memory
        elif memory_type == MemoryType.WORKING:
            self._add_working(memory)

        logger.debug(f"Memory added: {memory_type.value}")
        return memory

    def _add_short_term(self, memory: Memory) -> None:
        """Add to short-term memory with overflow handling"""
        self._short_term.append(memory)

        # Remove oldest if over limit
        while len(self._short_term) > self._max_short_term:
            removed = self._short_term.pop(0)
            # Optionally move to long-term if important
            if removed.importance > 0.7:
                self._long_term[removed.id] = removed
                removed.memory_type = MemoryType.LONG_TERM

    def _add_working(self, memory: Memory) -> None:
        """Add to working memory"""
        self._working.append(memory)

        while len(self._working) > self._max_working:
            self._working.pop(0)

    def get(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID"""
        # Search all stores
        for store in [self._long_term, self._episodic, self._semantic]:
            if memory_id in store:
                memory = store[memory_id]
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()
                return memory

        for memory in self._short_term + self._working:
            if memory.id == memory_id:
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()
                return memory

        return None

    def search(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[Memory]:
        """
        Search memories

        Args:
            query: Search query
            memory_type: Filter by type
            limit: Maximum results

        Returns:
            List of matching memories
        """
        results = []
        query_lower = query.lower()

        # Get memories to search
        memories = []
        if memory_type:
            if memory_type == MemoryType.SHORT_TERM:
                memories = self._short_term
            elif memory_type == MemoryType.LONG_TERM:
                memories = list(self._long_term.values())
            elif memory_type == MemoryType.EPISODIC:
                memories = list(self._episodic.values())
            elif memory_type == MemoryType.SEMANTIC:
                memories = list(self._semantic.values())
            elif memory_type == MemoryType.WORKING:
                memories = self._working
        else:
            memories = (
                self._short_term +
                list(self._long_term.values()) +
                list(self._episodic.values()) +
                list(self._semantic.values()) +
                self._working
            )

        # Simple text matching (could use embeddings)
        for memory in memories:
            if query_lower in memory.content.lower():
                results.append(memory)

        # Sort by importance and recency
        results.sort(
            key=lambda m: (m.importance, m.timestamp.timestamp()),
            reverse=True
        )

        return results[:limit]

    def get_context(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get recent context for LLM

        Args:
            limit: Maximum messages

        Returns:
            List of messages
        """
        # Combine short-term and working memory
        memories = self._short_term[-limit:] + self._working

        return [
            {"role": m.metadata.get("role", "user"), "content": m.content}
            for m in memories[-limit:]
        ]

    def clear(self, memory_type: Optional[MemoryType] = None) -> None:
        """Clear memories"""
        if memory_type is None:
            self._short_term = []
            self._long_term = {}
            self._episodic = {}
            self._semantic = {}
            self._working = []
        elif memory_type == MemoryType.SHORT_TERM:
            self._short_term = []
        elif memory_type == MemoryType.LONG_TERM:
            self._long_term = {}
        elif memory_type == MemoryType.EPISODIC:
            self._episodic = {}
        elif memory_type == MemoryType.SEMANTIC:
            self._semantic = {}
        elif memory_type == MemoryType.WORKING:
            self._working = []

    def consolidate(self) -> None:
        """Consolidate memories (move important short-term to long-term)"""
        to_move = []
        for memory in self._short_term:
            if memory.importance > 0.8 or memory.access_count > 3:
                to_move.append(memory)

        for memory in to_move:
            self._short_term.remove(memory)
            memory.memory_type = MemoryType.LONG_TERM
            self._long_term[memory.id] = memory

        logger.info(f"Consolidated {len(to_move)} memories to long-term")

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "short_term_count": len(self._short_term),
            "long_term_count": len(self._long_term),
            "episodic_count": len(self._episodic),
            "semantic_count": len(self._semantic),
            "working_count": len(self._working),
            "total": (
                len(self._short_term) +
                len(self._long_term) +
                len(self._episodic) +
                len(self._semantic) +
                len(self._working)
            )
        }
