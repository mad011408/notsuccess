"""
NEXUS AI Agent - Base Vector Store Interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Vector search result"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class BaseVectorStore(ABC):
    """Abstract base class for vector stores"""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the store"""
        pass

    @abstractmethod
    async def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add vectors to store"""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors"""
        pass

    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all vectors"""
        pass

    async def update(
        self,
        id: str,
        text: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a vector"""
        raise NotImplementedError

    async def get(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Get vectors by IDs"""
        raise NotImplementedError

    async def count(self) -> int:
        """Get total vector count"""
        raise NotImplementedError
