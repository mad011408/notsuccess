"""NEXUS AI Agent - Reranker"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from config.logging_config import get_logger


logger = get_logger(__name__)


class BaseReranker(ABC):
    """Base reranker class"""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Rerank documents"""
        pass


class Reranker(BaseReranker):
    """
    Document reranker

    Reranks retrieved documents for improved relevance
    """

    def __init__(
        self,
        model_name: str = "cross-encoder",
        llm_client=None
    ):
        self.model_name = model_name
        self.llm_client = llm_client
        self._cross_encoder = None

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to query

        Args:
            query: Search query
            documents: List of documents with 'content' key
            top_k: Number of top documents to return

        Returns:
            Reranked list of documents
        """
        if not documents:
            return []

        # Try cross-encoder first
        try:
            return await self._rerank_cross_encoder(query, documents, top_k)
        except Exception as e:
            logger.warning(f"Cross-encoder reranking failed: {e}")

        # Fall back to LLM-based reranking
        if self.llm_client:
            try:
                return await self._rerank_llm(query, documents, top_k)
            except Exception as e:
                logger.warning(f"LLM reranking failed: {e}")

        # Fall back to simple scoring
        return await self._rerank_simple(query, documents, top_k)

    async def _rerank_cross_encoder(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Rerank using cross-encoder model"""
        try:
            from sentence_transformers import CrossEncoder

            if self._cross_encoder is None:
                self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

            # Prepare pairs
            pairs = [(query, doc.get("content", "")) for doc in documents]

            # Get scores
            scores = self._cross_encoder.predict(pairs)

            # Add scores to documents
            for doc, score in zip(documents, scores):
                doc["rerank_score"] = float(score)

            # Sort by score
            documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

            if top_k:
                return documents[:top_k]
            return documents

        except ImportError:
            raise ImportError("sentence-transformers not installed")

    async def _rerank_llm(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Rerank using LLM scoring"""
        prompt = f"""Given the query and documents below, rate each document's relevance from 0-10.

Query: {query}

Documents:
"""
        for i, doc in enumerate(documents):
            content = doc.get("content", "")[:500]
            prompt += f"\n[{i}] {content}\n"

        prompt += "\nProvide scores as: document_index: score (one per line)"

        response = await self.llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        # Parse scores
        scores = {}
        for line in response.content.split('\n'):
            if ':' in line:
                try:
                    idx, score = line.split(':')
                    idx = int(idx.strip().strip('[]'))
                    score = float(score.strip())
                    scores[idx] = score
                except (ValueError, IndexError):
                    continue

        # Apply scores
        for i, doc in enumerate(documents):
            doc["rerank_score"] = scores.get(i, 0)

        documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        if top_k:
            return documents[:top_k]
        return documents

    async def _rerank_simple(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Simple keyword-based reranking"""
        import re

        query_terms = set(re.findall(r'\w+', query.lower()))

        for doc in documents:
            content = doc.get("content", "").lower()
            doc_terms = set(re.findall(r'\w+', content))

            # Calculate overlap
            overlap = len(query_terms & doc_terms)
            coverage = overlap / len(query_terms) if query_terms else 0

            # Consider existing score
            existing_score = doc.get("score", 0)
            doc["rerank_score"] = (existing_score + coverage) / 2

        documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        if top_k:
            return documents[:top_k]
        return documents


class CohereReranker(BaseReranker):
    """Reranker using Cohere Rerank API"""

    def __init__(self, api_key: str, model: str = "rerank-english-v2.0"):
        self.api_key = api_key
        self.model = model

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Rerank using Cohere API"""
        try:
            import cohere

            co = cohere.Client(self.api_key)

            docs = [doc.get("content", "") for doc in documents]

            results = co.rerank(
                query=query,
                documents=docs,
                model=self.model,
                top_n=top_k or len(documents)
            )

            # Create reranked list
            reranked = []
            for result in results:
                doc = documents[result.index].copy()
                doc["rerank_score"] = result.relevance_score
                reranked.append(doc)

            return reranked

        except ImportError:
            raise ImportError("cohere package not installed")


class EnsembleReranker(BaseReranker):
    """Combine multiple rerankers"""

    def __init__(self, rerankers: List[BaseReranker], weights: Optional[List[float]] = None):
        self.rerankers = rerankers
        self.weights = weights or [1.0] * len(rerankers)

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Ensemble reranking"""
        # Get scores from each reranker
        all_scores = []
        for reranker, weight in zip(self.rerankers, self.weights):
            try:
                results = await reranker.rerank(query, documents.copy())
                scores = {
                    r.get("content", "")[:100]: r.get("rerank_score", 0) * weight
                    for r in results
                }
                all_scores.append(scores)
            except Exception as e:
                logger.warning(f"Reranker failed: {e}")

        # Combine scores
        for doc in documents:
            key = doc.get("content", "")[:100]
            total_score = sum(scores.get(key, 0) for scores in all_scores)
            doc["rerank_score"] = total_score / len(all_scores)

        documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        if top_k:
            return documents[:top_k]
        return documents

