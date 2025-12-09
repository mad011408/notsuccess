"""
NEXUS AI Agent - ChromaDB Vector Store
"""

from typing import Optional, List, Dict, Any
import uuid

from .base_vector_store import BaseVectorStore, SearchResult
from config.logging_config import get_logger


logger = get_logger(__name__)


class ChromaDBStore(BaseVectorStore):
    """ChromaDB vector store implementation"""

    def __init__(
        self,
        collection_name: str = "nexus_memory",
        persist_directory: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None

    async def initialize(self) -> None:
        """Initialize ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings

            if self.persist_directory:
                self._client = chromadb.PersistentClient(path=self.persist_directory)
            else:
                self._client = chromadb.Client()

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            logger.info(f"ChromaDB initialized: {self.collection_name}")

        except ImportError:
            raise ImportError("chromadb package required: pip install chromadb")

    async def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add vectors to ChromaDB"""
        if not self._collection:
            await self.initialize()

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        if metadatas is None:
            metadatas = [{} for _ in texts]

        self._collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        return ids

    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search ChromaDB"""
        if not self._collection:
            await self.initialize()

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=filter
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                search_results.append(SearchResult(
                    id=id,
                    content=results["documents"][0][i] if results["documents"] else "",
                    score=1 - results["distances"][0][i] if results["distances"] else 0,
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {}
                ))

        return search_results

    async def delete(self, ids: List[str]) -> bool:
        """Delete from ChromaDB"""
        if not self._collection:
            await self.initialize()

        self._collection.delete(ids=ids)
        return True

    async def clear(self) -> None:
        """Clear collection"""
        if self._client:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name
            )

    async def count(self) -> int:
        """Get document count"""
        if not self._collection:
            await self.initialize()
        return self._collection.count()
