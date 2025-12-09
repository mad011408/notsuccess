"""NEXUS AI Agent - Pinecone Vector Store"""
from typing import Optional, List, Dict, Any
from .base_vector_store import BaseVectorStore, SearchResult

class PineconeStore(BaseVectorStore):
    def __init__(self, index_name: str = "nexus", api_key: Optional[str] = None):
        self.index_name = index_name
        self.api_key = api_key
        self._index = None

    async def initialize(self) -> None:
        from pinecone import Pinecone
        pc = Pinecone(api_key=self.api_key)
        self._index = pc.Index(self.index_name)

    async def add(self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> List[str]:
        import uuid
        ids = ids or [str(uuid.uuid4()) for _ in texts]
        vectors = [{"id": id, "values": emb, "metadata": {"text": txt, **(meta or {})}} for id, txt, emb, meta in zip(ids, texts, embeddings, metadatas or [{}]*len(texts))]
        self._index.upsert(vectors=vectors)
        return ids

    async def search(self, query_embedding: List[float], limit: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        results = self._index.query(vector=query_embedding, top_k=limit, include_metadata=True, filter=filter)
        return [SearchResult(id=m.id, content=m.metadata.get("text", ""), score=m.score, metadata=m.metadata) for m in results.matches]

    async def delete(self, ids: List[str]) -> bool:
        self._index.delete(ids=ids)
        return True

    async def clear(self) -> None:
        self._index.delete(delete_all=True)
