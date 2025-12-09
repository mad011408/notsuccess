"""NEXUS AI Agent - Base Embedder Interface"""
from abc import ABC, abstractmethod
from typing import List

class BaseEmbedder(ABC):
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Embed single text"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension"""
        pass
