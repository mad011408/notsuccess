"""
NEXUS AI Agent - Memory Retriever
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class RetrievedMemory:
    """A retrieved memory with relevance score"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]


class MemoryRetriever:
    """
    Retrieves relevant memories

    Features:
    - Semantic search
    - Keyword matching
    - Recency weighting
    """

    def __init__(self, embed_fn: Optional[Callable] = None):
        self._embed_fn = embed_fn
        self._memories: List[Dict[str, Any]] = []
        self._embeddings: List[List[float]] = []

    def set_embed_fn(self, embed_fn: Callable) -> None:
        """Set embedding function"""
        self._embed_fn = embed_fn

    def add(
        self,
        content: str,
        source: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a memory"""
        memory = {
            "content": content,
            "source": source,
            "metadata": metadata or {}
        }
        self._memories.append(memory)

        # Generate embedding if function available
        if self._embed_fn:
            embedding = self._embed_fn(content)
            self._embeddings.append(embedding)

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.0
    ) -> List[RetrievedMemory]:
        """
        Retrieve relevant memories

        Args:
            query: Search query
            limit: Max results
            min_score: Minimum relevance score

        Returns:
            List of retrieved memories
        """
        if self._embed_fn and self._embeddings:
            return await self._semantic_retrieve(query, limit, min_score)
        else:
            return self._keyword_retrieve(query, limit, min_score)

    async def _semantic_retrieve(
        self,
        query: str,
        limit: int,
        min_score: float
    ) -> List[RetrievedMemory]:
        """Semantic search using embeddings"""
        query_embedding = self._embed_fn(query)

        scored = []
        for i, (memory, embedding) in enumerate(zip(self._memories, self._embeddings)):
            score = self._cosine_similarity(query_embedding, embedding)
            if score >= min_score:
                scored.append((score, memory))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            RetrievedMemory(
                content=m["content"],
                score=s,
                source=m["source"],
                metadata=m["metadata"]
            )
            for s, m in scored[:limit]
        ]

    def _keyword_retrieve(
        self,
        query: str,
        limit: int,
        min_score: float
    ) -> List[RetrievedMemory]:
        """Simple keyword matching"""
        query_words = set(query.lower().split())
        scored = []

        for memory in self._memories:
            content_words = set(memory["content"].lower().split())
            overlap = len(query_words & content_words)
            score = overlap / max(len(query_words), 1)

            if score >= min_score:
                scored.append((score, memory))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            RetrievedMemory(
                content=m["content"],
                score=s,
                source=m["source"],
                metadata=m["metadata"]
            )
            for s, m in scored[:limit]
        ]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity"""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def clear(self) -> None:
        """Clear all memories"""
        self._memories = []
        self._embeddings = []

    def __len__(self) -> int:
        return len(self._memories)
