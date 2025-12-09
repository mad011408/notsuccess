"""NEXUS AI Agent - Local Embedder"""
from typing import List
from .base_embedder import BaseEmbedder

class LocalEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _init_model(self):
        if not self._model:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)

    async def embed(self, text: str) -> List[float]:
        self._init_model()
        return self._model.encode(text).tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._init_model()
        return self._model.encode(texts).tolist()

    @property
    def dimension(self) -> int:
        return 384
