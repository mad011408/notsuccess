"""NEXUS AI Agent - Cohere Embedder"""
from typing import List, Optional
import os
from .base_embedder import BaseEmbedder

class CohereEmbedder(BaseEmbedder):
    def __init__(self, model: str = "embed-english-v3.0", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        self._client = None

    async def _init_client(self):
        if not self._client:
            import cohere
            self._client = cohere.AsyncClient(api_key=self.api_key)

    async def embed(self, text: str) -> List[float]:
        await self._init_client()
        response = await self._client.embed(texts=[text], model=self.model, input_type="search_document")
        return response.embeddings[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        await self._init_client()
        response = await self._client.embed(texts=texts, model=self.model, input_type="search_document")
        return response.embeddings

    @property
    def dimension(self) -> int:
        return 1024
