"""NEXUS AI Agent - Retriever"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from config.logging_config import get_logger


logger = get_logger(__name__)


class RetrievalMethod(str, Enum):
    """Retrieval methods"""
    DENSE = "dense"  # Vector similarity
    SPARSE = "sparse"  # BM25/TF-IDF
    HYBRID = "hybrid"  # Combination


@dataclass
class RetrievalResult:
    """Retrieval result"""
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""


class BaseRetriever(ABC):
    """Base retriever class"""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """Retrieve relevant documents"""
        pass


class Retriever(BaseRetriever):
    """
    Document retriever

    Supports dense, sparse, and hybrid retrieval
    """

    def __init__(
        self,
        vector_store=None,
        embedder=None,
        method: RetrievalMethod = RetrievalMethod.DENSE
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.method = method

        # For sparse retrieval
        self._documents: List[Dict[str, Any]] = []
        self._index = None

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents

        Args:
            query: Search query
            top_k: Number of results
            filter_metadata: Optional metadata filter

        Returns:
            List of RetrievalResult
        """
        if self.method == RetrievalMethod.DENSE:
            return await self._dense_retrieve(query, top_k, filter_metadata)
        elif self.method == RetrievalMethod.SPARSE:
            return await self._sparse_retrieve(query, top_k)
        elif self.method == RetrievalMethod.HYBRID:
            return await self._hybrid_retrieve(query, top_k, filter_metadata)
        else:
            return []

    async def _dense_retrieve(
        self,
        query: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[RetrievalResult]:
        """Dense retrieval using vector similarity"""
        if not self.vector_store or not self.embedder:
            return []

        # Get query embedding
        query_embedding = await self.embedder.embed(query)

        # Search vector store
        results = await self.vector_store.search(
            embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )

        return [
            RetrievalResult(
                content=r.get("content", ""),
                score=r.get("score", 0.0),
                metadata=r.get("metadata", {}),
                source=r.get("metadata", {}).get("source", "")
            )
            for r in results
        ]

    async def _sparse_retrieve(
        self,
        query: str,
        top_k: int
    ) -> List[RetrievalResult]:
        """Sparse retrieval using BM25"""
        if not self._documents:
            return []

        # Simple TF-IDF based retrieval
        import re
        from collections import Counter

        query_terms = set(re.findall(r'\w+', query.lower()))
        scores = []

        for doc in self._documents:
            content = doc.get("content", "").lower()
            doc_terms = Counter(re.findall(r'\w+', content))

            # Simple term overlap score
            score = sum(doc_terms.get(term, 0) for term in query_terms)
            if doc_terms:
                score /= sum(doc_terms.values())

            scores.append((doc, score))

        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)

        return [
            RetrievalResult(
                content=doc.get("content", ""),
                score=score,
                metadata=doc.get("metadata", {}),
                source=doc.get("metadata", {}).get("source", "")
            )
            for doc, score in scores[:top_k]
        ]

    async def _hybrid_retrieve(
        self,
        query: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]]
    ) -> List[RetrievalResult]:
        """Hybrid retrieval combining dense and sparse"""
        # Get results from both methods
        dense_results = await self._dense_retrieve(query, top_k * 2, filter_metadata)
        sparse_results = await self._sparse_retrieve(query, top_k * 2)

        # Combine and deduplicate
        combined = {}

        for r in dense_results:
            key = r.content[:100]
            if key not in combined:
                combined[key] = r
            else:
                # Average scores
                combined[key].score = (combined[key].score + r.score) / 2

        for r in sparse_results:
            key = r.content[:100]
            if key not in combined:
                r.score *= 0.5  # Weight sparse results lower
                combined[key] = r
            else:
                combined[key].score = (combined[key].score + r.score * 0.5) / 2

        # Sort and return top_k
        results = sorted(combined.values(), key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents for sparse retrieval"""
        self._documents.extend(documents)

    def clear(self) -> None:
        """Clear documents"""
        self._documents.clear()


class MultiQueryRetriever(BaseRetriever):
    """Retriever that generates multiple query variations"""

    def __init__(
        self,
        base_retriever: Retriever,
        llm_client=None,
        num_queries: int = 3
    ):
        self.base_retriever = base_retriever
        self.llm_client = llm_client
        self.num_queries = num_queries

    async def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """Retrieve using multiple query variations"""
        queries = [query]

        # Generate query variations
        if self.llm_client:
            variations = await self._generate_variations(query)
            queries.extend(variations)

        # Retrieve for all queries
        all_results = []
        for q in queries:
            results = await self.base_retriever.retrieve(q, top_k)
            all_results.extend(results)

        # Deduplicate and rank
        unique_results = {}
        for r in all_results:
            key = r.content[:100]
            if key not in unique_results:
                unique_results[key] = r
            else:
                unique_results[key].score = max(unique_results[key].score, r.score)

        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: x.score,
            reverse=True
        )

        return sorted_results[:top_k]

    async def _generate_variations(self, query: str) -> List[str]:
        """Generate query variations using LLM"""
        prompt = f"""Generate {self.num_queries - 1} alternative versions of this search query.
Each version should express the same intent differently.

Original query: {query}

Provide only the alternative queries, one per line:"""

        response = await self.llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        variations = response.content.strip().split('\n')
        return [v.strip() for v in variations if v.strip()][:self.num_queries - 1]

