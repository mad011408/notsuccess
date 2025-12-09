"""NEXUS AI Agent - PGVector Store"""
from typing import Optional, List, Dict, Any
from .base_vector_store import BaseVectorStore, SearchResult

class PGVectorStore(BaseVectorStore):
    def __init__(self, connection_string: str, table_name: str = "nexus_vectors"):
        self.connection_string = connection_string
        self.table_name = table_name
        self._conn = None

    async def initialize(self) -> None:
        import asyncpg
        self._conn = await asyncpg.connect(self.connection_string)
        await self._conn.execute(f"CREATE EXTENSION IF NOT EXISTS vector")
        await self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id TEXT PRIMARY KEY, content TEXT, embedding vector(1536), metadata JSONB
            )
        """)

    async def add(self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> List[str]:
        import uuid, json
        ids = ids or [str(uuid.uuid4()) for _ in texts]
        for i, (id, txt, emb, meta) in enumerate(zip(ids, texts, embeddings, metadatas or [{}]*len(texts))):
            await self._conn.execute(f"INSERT INTO {self.table_name} VALUES ($1, $2, $3, $4)", id, txt, emb, json.dumps(meta))
        return ids

    async def search(self, query_embedding: List[float], limit: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        rows = await self._conn.fetch(f"SELECT id, content, metadata, 1 - (embedding <=> $1) as score FROM {self.table_name} ORDER BY embedding <=> $1 LIMIT $2", query_embedding, limit)
        import json
        return [SearchResult(id=r["id"], content=r["content"], score=r["score"], metadata=json.loads(r["metadata"])) for r in rows]

    async def delete(self, ids: List[str]) -> bool:
        await self._conn.execute(f"DELETE FROM {self.table_name} WHERE id = ANY($1)", ids)
        return True

    async def clear(self) -> None:
        await self._conn.execute(f"TRUNCATE TABLE {self.table_name}")
