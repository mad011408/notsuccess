"""NEXUS AI Agent - Qdrant Vector Store"""
from typing import Optional, List, Dict, Any
from .base_vector_store import BaseVectorStore, SearchResult

class QdrantStore(BaseVectorStore):
    def __init__(self, collection_name: str = "nexus", url: str = "localhost", port: int = 6333):
        self.collection_name = collection_name
        self.url = url
        self.port = port
        self._client = None

    async def initialize(self) -> None:
        from qdrant_client import QdrantClient
        self._client = QdrantClient(host=self.url, port=self.port)

    async def add(self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> List[str]:
        import uuid
        from qdrant_client.models import PointStruct
        ids = ids or [str(uuid.uuid4()) for _ in texts]
        points = [PointStruct(id=i, vector=emb, payload={"text": txt, **(meta or {})}) for i, (txt, emb, meta) in enumerate(zip(texts, embeddings, metadatas or [{}]*len(texts)))]
        self._client.upsert(collection_name=self.collection_name, points=points)
        return ids

    async def search(self, query_embedding: List[float], limit: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        results = self._client.search(collection_name=self.collection_name, query_vector=query_embedding, limit=limit)
        return [SearchResult(id=str(r.id), content=r.payload.get("text", ""), score=r.score, metadata=r.payload) for r in results]

    async def delete(self, ids: List[str]) -> bool:
        from qdrant_client.models import PointIdsList
        self._client.delete(collection_name=self.collection_name, points_selector=PointIdsList(points=[int(i) for i in ids]))
        return True

    async def clear(self) -> None:
        self._client.delete_collection(collection_name=self.collection_name)
