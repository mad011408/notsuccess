"""NEXUS AI Agent - OpenAI Embedder"""
from typing import List, Optional
import os
from .base_embedder import BaseEmbedder

class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    async def _init_client(self):
        if not self._client:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)

    async def embed(self, text: str) -> List[float]:
        await self._init_client()
        response = await self._client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        await self._init_client()
        response = await self._client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in response.data]

    @property
    def dimension(self) -> int:
        return 1536 if "small" in self.model else 3072
